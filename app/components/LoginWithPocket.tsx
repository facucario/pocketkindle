"use client";

import { useState } from "react";

const LoginWithPocket = () => {
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);

    try {
      const res = await fetch("/api/pocket/request");
      const { requestToken } = await res.json();

      // Store request token locally (or use a backend-secure storage mechanism)
      localStorage.setItem("pocketRequestToken", requestToken);

      const redirectUrl = `https://getpocket.com/auth/authorize?request_token=${requestToken}&redirect_uri=${process.env.NEXT_PUBLIC_REDIRECT_URI}`;
      window.location.href = redirectUrl;
    } catch (error) {
      console.error("Error during Pocket login:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleLogin}
      disabled={loading}
      className="p-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
    >
      {loading ? "Loading..." : "Login with Pocket"}
    </button>
  );
};

export default LoginWithPocket;