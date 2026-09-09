import { useEffect, useState } from "react";
import { Navigate, NavLink, Outlet, Route, Routes, useLocation, useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ClipboardList, FileImage, FileText, FolderKanban, Gauge, Map, Menu, Moon, Route as RouteIcon, Settings, ShieldCheck, Sun, X } from "lucide-react";
import { api } from "./api";
import { Button, Loading, Status } from "./components";
import { useWorkspace } from "./state";
import { CaseListPage, NewCasePage } from "./pages/cases";
import { OverviewPage } from "./pages/overview";
import { EvidencePage } from "./pages/evidence";
import { TimelinePage } from "./pages/timeline";
import { MapPage } from "./pages/map";
import { FindingsPage } from "./pages/findings";
import { CustodyPage } from "./pages/custody";
import { ReportsPage } from "./pages/reports";
import { SettingsPage } from "./pages/settings";

const nav=[{path:"overview",label:"Overview",icon:Gauge},{path:"evidence",label:"Evidence",icon:FileImage},{path:"timeline",label:"Timeline",icon:RouteIcon},{path:"map",label:"Map & route",icon:Map},{path:"findings",label:"Findings",icon:ClipboardList},{path:"custody",label:"Custody",icon:ShieldCheck},{path:"reports",label:"Reports",icon:FileText}];

function CaseShell(){
  const {caseId=""}=useParams();const {data:caseData,isLoading}=useQuery({queryKey:["case",caseId],queryFn:()=>api.case(caseId)});const {theme,toggleTheme}=useWorkspace();const [drawer,setDrawer]=useState(false);const navigate=useNavigate();const location=useLocation();
  useEffect(()=>setDrawer(false),[location.pathname]);
  if(isLoading)return <Loading/>;if(!caseData)return <Navigate to="/cases"/>;
  return <div className="app-shell"><aside className={drawer?"sidebar open":"sidebar"}><div className="brand"><div className="brand-mark">IT</div><div><strong>IMAGE TRACE</strong><span>Investigation workspace</span></div><button className="mobile-close" onClick={()=>setDrawer(false)} aria-label="Close navigation"><X/></button></div>
    <div className="case-switch"><small>Active case</small><strong>{caseData.name}</strong><span>{caseData.case_number}</span></div>
    <nav aria-label="Case workspace">{nav.map(item=><NavLink key={item.path} to={`/cases/${caseId}/${item.path}`}><item.icon size={17}/>{item.label}</NavLink>)}</nav>
    <div className="sidebar-foot"><NavLink to="/cases"><FolderKanban size={17}/>All cases</NavLink><NavLink to="/settings"><Settings size={17}/>Settings</NavLink></div></aside>
    {drawer&&<button className="drawer-scrim" onClick={()=>setDrawer(false)} aria-label="Close navigation"/>}
    <div className="shell-main"><header className="topbar"><button className="menu-button" onClick={()=>setDrawer(true)} aria-label="Open navigation"><Menu/></button><div className="top-case"><div><small>{caseData.case_number}</small><strong>{caseData.name}</strong></div><Status value={caseData.status}/></div><div className="integrity-summary"><ShieldCheck size={17}/><span>Local evidence controls active</span></div><button className="icon-button" onClick={toggleTheme} aria-label={`Switch to ${theme==="dark"?"light":"dark"} theme`}>{theme==="dark"?<Sun/>:<Moon/>}</button><Button onClick={()=>navigate(`/cases/${caseId}/reports`)} icon={FileText}>Generate report</Button></header>
      <main><Outlet context={{caseData}}/></main></div></div>;
}

export function App(){
  return <Routes><Route path="/" element={<Navigate to="/cases" replace/>}/><Route path="/cases" element={<CaseListPage/>}/><Route path="/cases/new" element={<NewCasePage/>}/><Route path="/cases/:caseId" element={<CaseShell/>}><Route index element={<Navigate to="overview" replace/>}/><Route path="overview" element={<OverviewPage/>}/><Route path="evidence" element={<EvidencePage/>}/><Route path="timeline" element={<TimelinePage/>}/><Route path="map" element={<MapPage/>}/><Route path="findings" element={<FindingsPage/>}/><Route path="custody" element={<CustodyPage/>}/><Route path="reports" element={<ReportsPage/>}/></Route><Route path="/settings" element={<SettingsPage/>}/><Route path="*" element={<Navigate to="/cases"/>}/></Routes>;
}
