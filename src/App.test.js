import { render, screen } from '@testing-library/react';
import App from './App';

test('renders the map navigation', () => {
  render(<App />);
  expect(screen.getByText(/main menu/i)).toBeInTheDocument();
  expect(screen.getByText(/view map/i)).toBeInTheDocument();
});
