import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MapView } from "./MapView";
import type { BlockGroupFeature } from "../types/api";

// Mock Leaflet since it requires DOM and we're testing component logic
vi.mock("leaflet", () => {
  const mockMap = {
    setView: vi.fn(),
    getZoom: vi.fn(() => 13),
    getContainer: vi.fn(() => document.createElement("div")),
    remove: vi.fn(),
  };
  const mockMarker = {
    setLatLng: vi.fn(),
    bindTooltip: vi.fn(),
    unbindTooltip: vi.fn(),
    getTooltip: vi.fn(() => null),
    addTo: vi.fn(() => mockMarker),
  };
  const mockLayer = {
    addTo: vi.fn(() => mockLayer),
    remove: vi.fn(),
    bringToBack: vi.fn(),
  };
  const mockGeoJSON = vi.fn(() => mockLayer);
  const mockTileLayer = vi.fn(() => ({ addTo: vi.fn() }));
  
  // Mock Marker class with prototype that can be modified
  const MockMarker = vi.fn(() => mockMarker);
  MockMarker.prototype = {
    options: { icon: null },
    setLatLng: vi.fn(),
    bindTooltip: vi.fn(),
    unbindTooltip: vi.fn(),
    getTooltip: vi.fn(() => null),
    addTo: vi.fn(() => mockMarker),
  };
  // Make prototype accessible
  Object.defineProperty(MockMarker, "prototype", {
    value: MockMarker.prototype,
    writable: true,
  });

  const leafletMock = {
    map: vi.fn(() => mockMap),
    tileLayer: mockTileLayer,
    marker: vi.fn(() => mockMarker), // lowercase 'marker' function
    Marker: MockMarker, // uppercase 'Marker' class
    geoJSON: mockGeoJSON,
    icon: vi.fn(),
  };

  return {
    default: leafletMock,
  };
});

describe("MapView", () => {
  beforeEach(() => {
    // Create a container div for the map
    document.body.innerHTML = '<div id="root"></div>';
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const defaultProps = {
    lat: 42.36,
    lon: -71.06,
    radiusMiles: 1.0,
  };

  it("renders map container", () => {
    const { container } = render(<MapView {...defaultProps} />);
    expect(container.querySelector(".map-view__container")).toBeInTheDocument();
  });

  it("displays caption with coordinates and radius", () => {
    render(<MapView {...defaultProps} />);
    expect(screen.getByText(/42\.3600.*-71\.0600/)).toBeInTheDocument();
    expect(screen.getByText(/1 mi/)).toBeInTheDocument();
  });

  it("shows legend when block groups are provided", () => {
    const blockGroups: BlockGroupFeature[] = [
      {
        geoid20: "123",
        natwalkind: 12.0,
        geometry: { type: "Polygon", coordinates: [[[-71, 42], [-71, 43], [-70, 43], [-70, 42], [-71, 42]]] },
      },
    ];
    render(<MapView {...defaultProps} blockGroups={blockGroups} nwiMean={10.0} />);
    expect(screen.getByText(/Well above avg/)).toBeInTheDocument();
    expect(screen.getByText(/No data/)).toBeInTheDocument();
  });

  it("does not show legend when no block groups", () => {
    render(<MapView {...defaultProps} blockGroups={[]} />);
    expect(screen.queryByText(/Well above avg/)).not.toBeInTheDocument();
  });

  it("does not show legend when blockGroups is null", () => {
    render(<MapView {...defaultProps} blockGroups={null} />);
    expect(screen.queryByText(/Well above avg/)).not.toBeInTheDocument();
  });

  it("handles label prop", () => {
    render(<MapView {...defaultProps} label="Cambridge, MA" />);
    // Label is handled by Leaflet marker tooltip, which is mocked
    // But we can verify the component accepts the prop without error
    expect(screen.getByText(/42\.3600/)).toBeInTheDocument();
  });

  it("handles null label", () => {
    render(<MapView {...defaultProps} label={null} />);
    expect(screen.getByText(/42\.3600/)).toBeInTheDocument();
  });

  it("handles empty label", () => {
    render(<MapView {...defaultProps} label="" />);
    expect(screen.getByText(/42\.3600/)).toBeInTheDocument();
  });

  it("handles missing nwiMean", () => {
    const blockGroups: BlockGroupFeature[] = [
      {
        geoid20: "123",
        natwalkind: 12.0,
        geometry: { type: "Polygon", coordinates: [[[-71, 42], [-71, 43], [-70, 43], [-70, 42], [-71, 42]]] },
      },
    ];
    render(<MapView {...defaultProps} blockGroups={blockGroups} nwiMean={null} />);
    // Should render but use "No data" color since nwiMean is null
    expect(screen.getByText(/No data/)).toBeInTheDocument();
  });

  it("handles block groups with null natwalkind", () => {
    const blockGroups: BlockGroupFeature[] = [
      {
        geoid20: "123",
        natwalkind: null,
        geometry: { type: "Polygon", coordinates: [[[-71, 42], [-71, 43], [-70, 43], [-70, 42], [-71, 42]]] },
      },
    ];
    render(<MapView {...defaultProps} blockGroups={blockGroups} nwiMean={10.0} />);
    // Should render with "No data" color
    expect(screen.getByText(/No data/)).toBeInTheDocument();
  });

  it("formats radius correctly in caption", () => {
    render(<MapView {...defaultProps} radiusMiles={2.5} />);
    expect(screen.getByText(/2\.5 mi/)).toBeInTheDocument();
  });

  it("handles fillHeight prop", () => {
    const { container } = render(<MapView {...defaultProps} fillHeight={true} />);
    const mapContainer = container.querySelector(".map-view__container");
    expect(mapContainer).toBeInTheDocument();
    // fillHeight affects inline styles, which are hard to test without rendering
    // But we can verify the component accepts the prop
  });
});
