import { createBrowserRouter, Outlet } from "react-router";
import ADRDReview from "./components/ADRDReview";
import FileUpload from "./components/FileUpload";
import ChartReview from "./components/ChartReview";

function Root() {
  return <Outlet />;
}

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Root,
    children: [
      { index: true, Component: FileUpload },
      { path: "review/:patientId", Component: ChartReview },
      { path: "prototype", Component: ADRDReview },
      { path: "*", Component: ADRDReview },
    ],
  },
]);
