import { useEffect, useRef } from "react";

interface Props {
  lines: string[];
}

export default function ConsoleOutput({ lines }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines.length]);

  return (
    <div className="console-output">
      <pre>
        {lines.map((line, i) => (
          <div key={i}>{line}</div>
        ))}
        <div ref={bottomRef} />
      </pre>
    </div>
  );
}
