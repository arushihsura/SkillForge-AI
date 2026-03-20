import { Children, useEffect, useMemo, useState } from "react";

export function Card({ children, className = "" }) {
  return (
    <div
      className={`sf-card h-full w-full rounded-2xl p-7 ${className}`.trim()}
      style={{
        background:
          "linear-gradient(180deg, rgba(15, 23, 42, 0.92), rgba(2, 6, 23, 0.96))",
      }}
    >
      {children}
    </div>
  );
}

function CardSwap({
  cardDistance = 60,
  verticalDistance = 70,
  delay = 5000,
  pauseOnHover = false,
  children,
}) {
  const cards = useMemo(() => Children.toArray(children).filter(Boolean), [children]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    if (cards.length <= 1) return;
    if (pauseOnHover && isPaused) return;

    const id = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % cards.length);
    }, delay);

    return () => clearInterval(id);
  }, [cards.length, delay, isPaused, pauseOnHover]);

  return (
    <div
      className="relative mx-auto w-full max-w-2xl"
      onMouseEnter={() => pauseOnHover && setIsPaused(true)}
      onMouseLeave={() => pauseOnHover && setIsPaused(false)}
      style={{ height: "100%" }}
    >
      {cards.map((card, index) => {
        const order = (index - activeIndex + cards.length) % cards.length;
        const xOffset = order * (cardDistance * 0.2);
        const yOffset = order * verticalDistance;
        const scale = Math.max(0.8, 1 - order * 0.07);
        const opacity = Math.max(0.28, 1 - order * 0.24);

        return (
          <div
            key={`swap-${index}`}
            style={{
              position: "absolute",
              top: 0,
              left: "50%",
              width: "100%",
              maxWidth: "640px",
              transform: `translate(-50%, ${yOffset}px) translateX(${xOffset}px) scale(${scale})`,
              zIndex: cards.length - order,
              opacity,
              filter: `blur(${order * 0.8}px)`,
              transition: "transform 700ms ease, opacity 700ms ease, filter 700ms ease",
              pointerEvents: order === 0 ? "auto" : "none",
            }}
          >
            {card}
          </div>
        );
      })}
    </div>
  );
}

export default CardSwap;
