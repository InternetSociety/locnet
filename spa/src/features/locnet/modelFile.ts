const padTimePart = (value: number): string => value.toString().padStart(2, '0');

export const getModelFileName = (
  iso_3: string,
  localTime: Date = new Date(),
): string => {
  const date = [
    localTime.getFullYear(),
    padTimePart(localTime.getMonth() + 1),
    padTimePart(localTime.getDate()),
  ].join('-');
  const time = [
    padTimePart(localTime.getHours()),
    padTimePart(localTime.getMinutes()),
    padTimePart(localTime.getSeconds()),
  ].join('-');

  return `cn_model_${iso_3.toLowerCase()}_${date}_${time}.json`;
};
