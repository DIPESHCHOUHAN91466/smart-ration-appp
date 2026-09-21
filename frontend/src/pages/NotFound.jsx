import { Link } from "react-router-dom";
import { EmptyState } from "../components/EmptyState";

export default function NotFound() {
  return (
    <div className="center-panel">
      <EmptyState title="Page not found" text="The page you're looking for doesn't exist." />
      <p style={{ textAlign: "center" }}>
        <Link to="/">Go back home</Link>
      </p>
    </div>
  );
}
