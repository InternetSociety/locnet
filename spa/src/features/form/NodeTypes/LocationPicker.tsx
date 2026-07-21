import { Map as MapLibreMap, Marker } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
} from 'react';
import { clamp } from 'lodash-es';
import {
  useStaticFormTsContext,
  type FormPath,
  type ModelPath,
} from '../FormProvider';
import { Text } from '../Intl';
import type { NetworkElement } from './NetworkElements';
import type { BoundsResponse } from '../../locnet/api-generated-client';
import { useBoundsData } from './useBoundsData';
import styles from './LocationPicker.module.css';

// Countries that straddle the antimeridian. For these we skip longitude bounds
// validation (see issue) because their bounding box spans -180..180.
const ANTIMERIDIAN_ISO3 = ['RUS', 'ATA', 'FJI'];

// The style URL is provided by the backend (see /api/map_config) so the tile
// provider and its API key stay server-side. Cache the lookup for the session.
let mapStyleUrlPromise: Promise<string> | undefined;
const getMapStyleUrl = (): Promise<string> => {
  if (!mapStyleUrlPromise) {
    mapStyleUrlPromise = fetch('/api/map_config')
      .then((response) => response.json())
      .then((body: { style_url: string }) => body.style_url);
  }
  return mapStyleUrlPromise;
};

const isAntimeridianCountry = (bounds: BoundsResponse): boolean =>
  ANTIMERIDIAN_ISO3.includes(bounds.iso_3) ||
  (bounds.bbox_west === -180 && bounds.bbox_east === 180);

type RenderLocationPickerProps = {
  id: FormPath;
  modelPath: ModelPath;
  locationIndex: number;
  defaultLatitude: number;
  defaultLongitude: number;
};

export const RenderLocationPicker = ({
  id,
  modelPath,
  locationIndex,
  defaultLatitude,
  defaultLongitude,
}: RenderLocationPickerProps) => {
  const { useFormAndModel } = useStaticFormTsContext();
  const boundsData = useBoundsData();

  const latId = `${id}.${
    'latitude' satisfies keyof NetworkElement
  }` as FormPath;
  const latModelPath = `${modelPath}.${
    'latitude' satisfies keyof NetworkElement
  }` as ModelPath;
  const lonId = `${id}.${
    'longitude' satisfies keyof NetworkElement
  }` as FormPath;
  const lonModelPath = `${modelPath}.${
    'longitude' satisfies keyof NetworkElement
  }` as ModelPath;

  const [latitude, setLatitude] = useFormAndModel(
    latId,
    latModelPath,
    defaultLatitude,
  );
  const [longitude, setLongitude] = useFormAndModel(
    lonId,
    lonModelPath,
    defaultLongitude,
  );

  // If a location was created before the bounds were available, initialise its
  // coordinates to the country centroid once, the first time bounds load.
  const didInitCentroid = useRef(false);
  useEffect(() => {
    if (didInitCentroid.current || !boundsData) return;
    if (latitude === 0 && longitude === 0) {
      setLatitude(boundsData.centroid_lat);
      setLongitude(boundsData.centroid_long);
    }
    didInitCentroid.current = true;
  }, [boundsData, latitude, longitude, setLatitude, setLongitude]);

  const isAntimeridian = boundsData ? isAntimeridianCountry(boundsData) : false;

  // Local text state for the inputs so the user can type freely (e.g. "-", "5.")
  // while the numeric form value only updates for valid, in-bounds coordinates.
  const [latText, setLatText] = useState(() => String(latitude));
  const [lonText, setLonText] = useState(() => String(longitude));

  useEffect(() => {
    if (parseFloat(latText) !== latitude) {
      setLatText(String(latitude));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [latitude]);

  useEffect(() => {
    if (parseFloat(lonText) !== longitude) {
      setLonText(String(longitude));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [longitude]);

  const latNum = parseFloat(latText);
  const lonNum = parseFloat(lonText);

  const latInvalid = boundsData
    ? Number.isNaN(latNum) ||
      latNum < boundsData.bbox_south ||
      latNum > boundsData.bbox_north
    : false;

  const lonInvalid =
    boundsData && !isAntimeridian
      ? Number.isNaN(lonNum) ||
        lonNum < boundsData.bbox_west ||
        lonNum > boundsData.bbox_east
      : false;

  // Refs so the map event handlers always see the latest bounds / flags.
  const boundsRef = useRef(boundsData);
  boundsRef.current = boundsData;
  const isAntimeridianRef = useRef(isAntimeridian);
  isAntimeridianRef.current = isAntimeridian;
  const coordsRef = useRef({ lat: latitude, lng: longitude });
  coordsRef.current = { lat: latitude, lng: longitude };

  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const markerRef = useRef<Marker | null>(null);

  // Clamp a position to the bounding box (longitude unrestricted for
  // antimeridian countries) and store it. Keeps the marker inside the country.
  const applyMarkerPosition = useCallback(
    (rawLng: number, rawLat: number) => {
      const bounds = boundsRef.current;
      if (!bounds) return;
      const lat = clamp(rawLat, bounds.bbox_south, bounds.bbox_north);
      const lng = isAntimeridianRef.current
        ? rawLng
        : clamp(rawLng, bounds.bbox_west, bounds.bbox_east);
      setLatitude(lat);
      setLongitude(lng);
      markerRef.current?.setLngLat([lng, lat]);
    },
    [setLatitude, setLongitude],
  );

  // Create the map once bounds are available.
  useEffect(() => {
    if (!boundsData || mapRef.current) return;
    const container = mapContainerRef.current;
    if (!container) return;

    let cancelled = false;
    const countryBounds: [[number, number], [number, number]] = [
      [boundsData.bbox_west, boundsData.bbox_south],
      [boundsData.bbox_east, boundsData.bbox_north],
    ];

    getMapStyleUrl()
      .then((styleUrl) => {
        if (cancelled || mapRef.current) return;

        let map: MapLibreMap;
        try {
          map = new MapLibreMap({
            container,
            style: styleUrl,
            center: [coordsRef.current.lng, coordsRef.current.lat],
            zoom: 3,
            // MapLibre supports zoom levels down to -2. This lets us set the
            // country-derived minimum zoom once the initial fit is complete.
            minZoom: -2,
          });
        } catch (error) {
          console.error('Failed to initialise MapLibre map', error);
          return;
        }
        mapRef.current = map;

        map.on('load', () => {
          map.fitBounds(countryBounds, { animate: false, padding: 20 });
          const countryCenter = map.getCenter();
          const countryZoom = map.getZoom();
          const minZoom = Math.max(-2, countryZoom - 2);

          // Use the viewport at two levels farther out as the map boundary.
          // This preserves panning limits while permitting the requested zoom.
          map.jumpTo({ center: countryCenter, zoom: minZoom });
          map.setMaxBounds(map.getBounds());
          map.jumpTo({ center: countryCenter, zoom: countryZoom });
          map.setMinZoom(minZoom);
        });

        const marker = new Marker({ draggable: true, color: '#e53935' })
          .setLngLat([coordsRef.current.lng, coordsRef.current.lat])
          .addTo(map);
        markerRef.current = marker;

        marker.on('dragend', () => {
          const { lng, lat } = marker.getLngLat();
          applyMarkerPosition(lng, lat);
        });

        map.on('click', (event) => {
          applyMarkerPosition(event.lngLat.lng, event.lngLat.lat);
        });
      })
      .catch((error) => {
        console.error('Failed to load map style', error);
      });

    return () => {
      cancelled = true;
    };
  }, [boundsData, applyMarkerPosition]);

  // Tear down the map on unmount.
  useEffect(
    () => () => {
      markerRef.current?.remove();
      markerRef.current = null;
      mapRef.current?.remove();
      mapRef.current = null;
    },
    [],
  );

  const handleLatChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const { value } = e.target;
      setLatText(value);
      const bounds = boundsRef.current;
      const num = parseFloat(value);
      if (!bounds || Number.isNaN(num)) return;
      if (num >= bounds.bbox_south && num <= bounds.bbox_north) {
        setLatitude(num);
      }
    },
    [setLatitude],
  );

  const handleLonChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const { value } = e.target;
      setLonText(value);
      const bounds = boundsRef.current;
      const num = parseFloat(value);
      if (!bounds || Number.isNaN(num)) return;
      if (isAntimeridianRef.current) {
        setLongitude(num);
        return;
      }
      if (num >= bounds.bbox_west && num <= bounds.bbox_east) {
        setLongitude(num);
      }
    },
    [setLongitude],
  );

  const handleUpdateMap = useCallback(() => {
    if (latInvalid || lonInvalid) return;
    const coordinates: [number, number] = [longitude, latitude];
    markerRef.current?.setLngLat(coordinates);
    mapRef.current?.flyTo({ center: coordinates, zoom: 15 });
  }, [latInvalid, lonInvalid, latitude, longitude]);

  return (
    <div className={styles.locationPickerContainer}>
      <h3 className={styles.locationPickerHeading}>
        <Text intlId="location_picker" />
      </h3>
      <div
        ref={mapContainerRef}
        className={styles.map}
        data-testid={`location-${locationIndex}-map`}
      />
      <div className={styles.coordinatesRow}>
        <label className={styles.coordinateLabel}>
          <span>
            <Text intlId="latitude" />
          </span>
          <input
            id={latId}
            name={latId}
            type="number"
            step="any"
            value={latText}
            onChange={handleLatChange}
            aria-invalid={latInvalid}
            className={
              latInvalid
                ? `${styles.coordinateInput} ${styles.invalid}`
                : styles.coordinateInput
            }
            data-testid={`location-${locationIndex}-latitude`}
          />
        </label>
        <label className={styles.coordinateLabel}>
          <span>
            <Text intlId="longitude" />
          </span>
          <input
            id={lonId}
            name={lonId}
            type="number"
            step="any"
            value={lonText}
            onChange={handleLonChange}
            aria-invalid={lonInvalid}
            className={
              lonInvalid
                ? `${styles.coordinateInput} ${styles.invalid}`
                : styles.coordinateInput
            }
            data-testid={`location-${locationIndex}-longitude`}
          />
        </label>
        <button
          type="button"
          onClick={handleUpdateMap}
          disabled={!boundsData || latInvalid || lonInvalid}
          className={styles.updateMapButton}
          data-testid={`location-${locationIndex}-update-map`}
        >
          <Text intlId="update_map" />
        </button>
      </div>
    </div>
  );
};
