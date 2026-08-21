import { useEffect } from 'react';
import { useMap } from 'react-leaflet';

const isValidOrigin = origin => (
  Number.isFinite(Number(origin?.latitude)) && Number.isFinite(Number(origin?.longitude))
);

export const FlyToRenderer = ({ flyTo }) => {
  const map = useMap();

  useEffect(() => {
    if (isValidOrigin(flyTo)) {
      map.flyTo([Number(flyTo.latitude), Number(flyTo.longitude)]);
    }
  }, [flyTo, map]);

  return null;
};
