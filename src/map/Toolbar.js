import React, { useState } from 'react';
import { useAsync } from 'react-async';
import { LoadingButton } from '@mui/lab';
import { Search } from '@mui/icons-material';
import { TextField, Button } from '@mui/material';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000';

async function getTweets(city, distance, signal) {
  const query = new URLSearchParams({ city: city.trim(), distance: String(distance) });
  const response = await fetch(`${API_BASE_URL}/search/tweets?${query}`, { signal });
  if (!response.ok) {
    throw new Error(`Search failed with status ${response.status}`);
  }
  const { origin, features } = await response.json();
  return {origin, features};
}

const isDistanceValid = distance => {
  const value = Number(distance);
  return !Number.isFinite(value) || value <= 0;
};
export const Toolbar = (props)  => {
  const [address, setAddress] = useState(props.location); 
  const [addressErr, setAddressErr] = useState("");

  const [distance, setDistance] = useState(props.distance);

  const { run: search, isPending } = useAsync({
    deferFn: ([city, distance], {signal}) => getTweets(city, distance, signal),
    onResolve: (tweetResponse) => {
      const {origin, features} = tweetResponse;
      setAddressErr("");
      props.onSearch({ origin, features });
      
    },
    onReject: (error) => {
      setAddressErr("Invalid address found.");
      console.error(error);
    }
  });

  const handleSearch = () => {
    if (!address.trim()) {
      setAddressErr("Enter a city or address.");
      return;
    }
    if (isDistanceValid(distance)) return;
    search(address, distance);
  };

  return (
    <div style={{ height: '4.9rem', marginTop: '1rem'}}>
      <Button onClick={() => props.onMenuClick()}>Open Menu</Button>
      <TextField
        label='Address'
        value={address}
        error={addressErr !== ""}
        helperText={addressErr}
        onChange={(event) => setAddress(event.target.value)}
      />
      <TextField
        label='Distance (in miles)'
        type='number'
        value={distance}
        inputProps={{ min: 0.1, step: 0.1 }}
        error={isDistanceValid(distance)}
        helperText={isDistanceValid(distance) ? "Distance must be a positive float." : ""}
        onChange={(event) => setDistance(event.target.value)}
      />
      <LoadingButton
        onClick={handleSearch}
        loading={isPending}
        endIcon={<Search/>}
        loadingPosition="end">
          Search
      </LoadingButton>
    </div>
  );
};
