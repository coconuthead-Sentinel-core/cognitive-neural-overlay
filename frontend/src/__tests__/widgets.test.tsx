import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Sparkline, Donut, HeatMap } from "../widgets";

describe("Sparkline", () => {
  it("renders a polyline + area path for 2+ points", () => {
    const { container } = render(<Sparkline values={[1, 2, 3, 4]} />);
    expect(container.querySelector("svg")).toBeInTheDocument();
    expect(container.querySelector("polyline")).toBeInTheDocument();
    expect(container.querySelector("path")).toBeInTheDocument();
  });

  it("shows fallback when fewer than 2 points", () => {
    render(<Sparkline values={[5]} />);
    expect(screen.getByText(/need ≥ 2 data points/)).toBeInTheDocument();
  });
});

describe("Donut", () => {
  it("renders a slice + legend for each entry", () => {
    const data = [
      { sublayer: "Analytical Layer", count: 3 },
      { sublayer: "Output Layer",     count: 1 },
    ];
    const { container } = render(<Donut data={data} />);
    const paths = container.querySelectorAll("path");
    expect(paths.length).toBe(2);
    expect(screen.getByText("Analytical Layer")).toBeInTheDocument();
    expect(screen.getByText("Output Layer")).toBeInTheDocument();
    // Total in the middle of the donut
    expect(screen.getByText("4")).toBeInTheDocument();
  });

  it("renders empty state when data is empty", () => {
    render(<Donut data={[]} />);
    expect(screen.getByText(/no data yet/i)).toBeInTheDocument();
  });

  it("handles single-slice (full-circle) without crashing", () => {
    const { container } = render(<Donut data={[{ sublayer: "Output Layer", count: 5 }]} />);
    expect(container.querySelectorAll("path").length).toBe(1);
    expect(screen.getByText("5")).toBeInTheDocument();
  });
});

describe("HeatMap", () => {
  it("renders a row per modality + col per persona", () => {
    const matrix = [
      { modality: "text",  persona_style: "technical", count: 3 },
      { modality: "text",  persona_style: "direct",    count: 1 },
      { modality: "voice", persona_style: "technical", count: 2 },
    ];
    render(<HeatMap matrix={matrix} />);
    // headers
    expect(screen.getByText("technical")).toBeInTheDocument();
    expect(screen.getByText("direct")).toBeInTheDocument();
    // row headers
    expect(screen.getByText("text")).toBeInTheDocument();
    expect(screen.getByText("voice")).toBeInTheDocument();
    // counts
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("renders empty placeholder when no matrix data", () => {
    render(<HeatMap matrix={[]} />);
    expect(screen.getByText(/no runs yet/i)).toBeInTheDocument();
  });
});
