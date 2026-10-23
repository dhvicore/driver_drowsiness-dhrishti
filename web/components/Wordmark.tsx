import Link from "next/link";
import { LogoMark } from "@/components/Logo";

export function Wordmark({ href = "/" }: { href?: string }) {
  return (
    <Link href={href} className="group flex items-center gap-2.5">
      <LogoMark className="h-8 w-auto" />
      <span className="text-[15px] font-extrabold tracking-[-0.03em] text-ink">
        Drishti
      </span>
    </Link>
  );
}
