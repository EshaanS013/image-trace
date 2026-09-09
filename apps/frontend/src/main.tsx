import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { App } from "./App";
import { WorkspaceProvider } from "./state";
import "./styles.css";

const client=new QueryClient({defaultOptions:{queries:{staleTime:10_000,retry:1}}});
createRoot(document.getElementById("root")!).render(<StrictMode><QueryClientProvider client={client}><WorkspaceProvider><BrowserRouter><App/></BrowserRouter></WorkspaceProvider></QueryClientProvider></StrictMode>);

