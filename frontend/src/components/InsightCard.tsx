import React from "react";

type InsightCardProps = {
  title: string;
  children: React.ReactNode;
};

export function InsightCard({ title, children }: InsightCardProps) {
  return (
    <div className="card-section">
      <h3 style={{ margin: "0 0 6px" }}>{title}</h3>
      {children}
    </div>
  );
}



