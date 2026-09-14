import { render, screen } from '@testing-library/react';
import App from './App';

test('renders coastal threat dashboard', async () => {
  global.fetch = jest.fn((url) => {
    if (url.includes('/history')) {
      return Promise.resolve({ ok: true, json: async () => [] });
    }
    if (url.includes('/coastal/latest')) {
      return Promise.resolve({ ok: true, json: async () => [] });
    }
    if (url.includes('/risk-zones')) {
      return Promise.resolve({ ok: true, json: async () => ({ type: 'FeatureCollection', features: [] }) });
    }
    if (url.includes('/alerts')) {
      return Promise.resolve({ ok: true, json: async () => [] });
    }
    if (url.includes('/coastal/anomalies')) {
      return Promise.resolve({ ok: true, json: async () => [] });
    }
    return Promise.resolve({ ok: true, json: async () => ({ alert_level: 'LOW', confidence: 0.9 }) });
  });

  render(<App />);
  expect((await screen.findAllByText(/No weather data available for Mumbai/i)).length).toBeGreaterThan(0);
});
