"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    if (api.getToken()) {
      router.replace("/dashboard");
    } else {
      router.replace("/auth/login");
    }
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <span className="spinner mx-auto mb-3 block h-6 w-6 text-brand-500" />
        <p className="text-sm text-gray-400">Loading...</p>
      </div>
    </div>
  );
}
