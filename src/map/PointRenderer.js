import { Popup, Marker } from 'react-leaflet';

export const PointRenderer = (props) => {
  const { features } = props;
  return (
    <>
      {features && features.length && features.map((feature, index) => {
        const [longitude, latitude] = feature.geometry.coordinates;
        return (
          <Marker key={feature.id || index} position={[latitude, longitude]}>
            <Popup>
              {Object.keys(feature.properties).filter(key => typeof feature.properties[key] === 'string').map(key => {
                return ( <div key={key}> <b>{key.toUpperCase()}</b> {feature.properties[key]} <br/> </div>);
              })}
            </Popup>
          </Marker>
        );
      })}
    </>
  )
};
