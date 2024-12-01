import { NextResponse } from "next/server";
import axios from "axios";

export async function GET(request: Request) {
  const consumerKey = process.env.POCKET_CONSUMER_KEY!;
  const requestToken = localStorage.getItem("pocketRequestToken");


  if (!requestToken) {
    return NextResponse.json({ error: "Missing request token" }, { status: 400 });
  }

  try {
    const response = await axios.post(
      "https://getpocket.com/v3/oauth/authorize",
      {
        consumer_key: consumerKey,
        code: requestToken,
      },
      {
        headers: {
          "Content-Type": "application/json",
          "X-Accept": "application/json",
        },
      }
    );

    const { access_token: accessToken, username } = response.data;
    return NextResponse.json({ accessToken, username });
  } catch (error: any) {
    console.error("Error in Pocket callback API:", error.message);
    return NextResponse.json(
      { error: error.message },
      { status: 500 }
    );
  }
}