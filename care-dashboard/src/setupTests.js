// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

jest.mock('react-leaflet', () => {
	const React = require('react');
	const passthrough = ({ children }) => React.createElement('div', null, children);
	return {
		GeoJSON: passthrough,
		MapContainer: passthrough,
		Marker: passthrough,
		Popup: passthrough,
		TileLayer: passthrough,
	};
});

jest.mock('leaflet', () => ({
	Icon: function Icon() {},
}));
