"use client";

import { useEffect, useState } from "react";

const PocketCallbackHandler = () => {
  const [status, setStatus] = useState<string>("Authorizing...");

  useEffect(() => {
    const pocketRequestToken = localStorage.getItem("pocketRequestToken");

    if (!pocketRequestToken) {
      setStatus("Request token is missing or expired.");
      return;
    }

    const authorizePocket = async () => {
      try {
        const response = await fetch(`/api/pocket/callback`, {
          method: "GET",
          headers: {
            "pocket-request-token": pocketRequestToken,
          },
        });

        const data = await response.json();

        if (response.ok) {
          setStatus(`Success! Welcome, ${data.username}.`);
          // Handle successful login (e.g., store access token in state or backend)
        } else {
          setStatus(`Error: ${data.error}`);
        }
      } catch (error) {
        console.error("Error authorizing Pocket:", error);
        setStatus("Failed to authorize.");
      }
    };

    authorizePocket();
  }, []);

  return <div>{status}</div>;
};

export default PocketCallbackHandler;