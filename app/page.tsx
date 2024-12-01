import LoginWithPocket from "./components/LoginWithPocket";

export default function Home() {
  const consumerKey = process.env.POCKET_CONSUMER_KEY!;
  const redirectUri = process.env.NEXT_PUBLIC_REDIRECT_URI!;

  console.log("consumerKey: ", consumerKey)
  console.log("redirectUri: ", redirectUri)


  return (
    <main className="flex items-center justify-center min-h-screen bg-gray-100">
      <LoginWithPocket />
    </main>
  );
}
