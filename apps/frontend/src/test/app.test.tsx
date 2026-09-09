import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../App";
import { WorkspaceProvider } from "../state";

const caseRecord={id:"case-1",case_number:"CASE-001",name:"Synthetic review",description:"Fixture",analyst_name:"Analyst",status:"open",case_timezone:null,created_at:"2026-01-01T00:00:00Z",updated_at:"2026-01-01T00:00:00Z"};
afterEach(()=>cleanup());
beforeEach(()=>{localStorage.clear();vi.stubGlobal("fetch",vi.fn(async(input:RequestInfo|URL)=>{const url=String(input);if(url.endsWith("/cases"))return new Response(JSON.stringify({items:[caseRecord],total:1,page:1,page_size:25}),{status:200,headers:{"Content-Type":"application/json"}});if(url.endsWith("/cases/case-1"))return new Response(JSON.stringify(caseRecord),{status:200,headers:{"Content-Type":"application/json"}});if(url.endsWith("/findings"))return new Response(JSON.stringify([]),{status:200,headers:{"Content-Type":"application/json"}});return new Response(JSON.stringify({items:[],total:0,page:1,page_size:200}),{status:200,headers:{"Content-Type":"application/json"}})}));});
function view(path:string){return render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><WorkspaceProvider><MemoryRouter initialEntries={[path]}><App/></MemoryRouter></WorkspaceProvider></QueryClientProvider>)}
describe("IMAGE TRACE interface",()=>{it("lists cases and exposes new-case action",async()=>{view("/cases");expect(await screen.findByText("Synthetic review")).toBeInTheDocument();expect(screen.getByRole("button",{name:/new case/i})).toBeInTheDocument()});it("switches theme",async()=>{view("/cases");await userEvent.click(screen.getByRole("button",{name:/toggle theme/i}));expect(document.querySelector("[data-theme='dark']")).toBeInTheDocument()});it("shows case navigation",async()=>{view("/cases/case-1/overview");expect(await screen.findByRole("navigation",{name:/case workspace/i})).toBeInTheDocument();expect(screen.getByRole("link",{name:/evidence/i})).toBeInTheDocument()})});
