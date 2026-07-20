import { useStaticFormTsContext } from '../FormProvider';
import type { BoundsResponse } from '../../locnet/api-generated-client';

type ApiError = { type: 'error'; message: string };

const isBoundsResponse = (
  value: BoundsResponse | ApiError | undefined,
): value is BoundsResponse => Boolean(value) && !(value && 'type' in value);

/**
 * Reads the currently loaded country bounds (centroid + bounding box) from the
 * form store. Returns undefined while loading or on error.
 */
export const useBoundsData = (): BoundsResponse | undefined => {
  const { useWatchFormStore } = useStaticFormTsContext();
  const bounds = useWatchFormStore(
    'api.bounds',
    undefined as BoundsResponse | ApiError | undefined,
  );
  return isBoundsResponse(bounds) ? bounds : undefined;
};
