import { NextResponse } from "next/server";
import axios from "axios";

export async function GET() {
  const consumerKey = process.env.POCKET_CONSUMER_KEY!;
  const redirectUri = process.env.NEXT_PUBLIC_REDIRECT_URI!;

  try {
    const response = await axios.post(
      "https://getpocket.com/v3/oauth/request",
      {
        consumer_key: consumerKey,
        redirect_uri: redirectUri,
      },
      {
        headers: {
          "Content-Type": "application/json",
          "X-Accept": "application/json",
        },
      }
    );

    const requestToken = response.data.code;

    // Send the request token back to the client
    return NextResponse.json({ requestToken });
  } catch (error: any) {
    console.error("Error in Pocket request API:", error.message);
    return NextResponse.json(
      { error: error.message },
      { status: 500 }
    );
  }
}