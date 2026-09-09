import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

type WorkspaceState={selectedId:string|null;setSelectedId:(id:string|null)=>void;search:string;setSearch:(value:string)=>void;theme:"light"|"dark";toggleTheme:()=>void};
const Context=createContext<WorkspaceState|null>(null);
export function WorkspaceProvider({children}:{children:ReactNode}){
  const [selectedId,setSelectedId]=useState<string|null>(null); const [search,setSearch]=useState("");
  const [theme,setTheme]=useState<"light"|"dark">(()=>localStorage.getItem("image-trace-theme")==="dark"?"dark":"light");
  const toggleTheme=()=>setTheme(current=>{const next=current==="dark"?"light":"dark";localStorage.setItem("image-trace-theme",next);return next;});
  const value=useMemo(()=>({selectedId,setSelectedId,search,setSearch,theme,toggleTheme}),[selectedId,search,theme]);
  return <Context.Provider value={value}><div data-theme={theme}>{children}</div></Context.Provider>;
}
export function useWorkspace(){const value=useContext(Context);if(!value)throw new Error("WorkspaceProvider missing");return value;}

