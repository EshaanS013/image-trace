import * as Dialog from "@radix-ui/react-dialog";
import { AlertTriangle, CheckCircle2, LoaderCircle, X, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

export function Button({children,variant="primary",icon:Icon,...props}:{children:ReactNode;variant?:"primary"|"secondary"|"quiet"|"danger";icon?:LucideIcon}&React.ButtonHTMLAttributes<HTMLButtonElement>){return <button className={`button ${variant}`} {...props}>{Icon&&<Icon size={16}/>}<span>{children}</span></button>}
export function Status({value}:{value:string}){const normalized=value.toLowerCase().replaceAll("_"," ");return <span className={`status status-${value}`}><span aria-hidden="true"/>{normalized}</span>}
export function Field({label,children,hint}:{label:string;children:ReactNode;hint?:string}){return <label className="field"><span>{label}</span>{children}{hint&&<small>{hint}</small>}</label>}
export function Empty({title,body,action}:{title:string;body:string;action?:ReactNode}){return <div className="empty"><div className="empty-mark" aria-hidden="true">◎</div><h3>{title}</h3><p>{body}</p>{action}</div>}
export function Loading({label="Loading workspace"}:{label?:string}){return <div className="loading"><LoaderCircle className="spin" size={20}/><span>{label}</span></div>}
export function ErrorState({message}:{message:string}){return <div className="error-state" role="alert"><AlertTriangle size={19}/><div><strong>Unable to load this view</strong><p>{message}</p></div></div>}
export function Modal({open,onOpenChange,title,description,children}:{open:boolean;onOpenChange:(open:boolean)=>void;title:string;description?:string;children:ReactNode}){return <Dialog.Root open={open} onOpenChange={onOpenChange}><Dialog.Portal><Dialog.Overlay className="dialog-overlay"/><Dialog.Content className="dialog-content"><Dialog.Title>{title}</Dialog.Title>{description&&<Dialog.Description>{description}</Dialog.Description>}<Dialog.Close className="dialog-close" aria-label="Close"><X size={18}/></Dialog.Close>{children}</Dialog.Content></Dialog.Portal></Dialog.Root>}
export function Toast({message,onClose}:{message:string;onClose:()=>void}){return <div className="toast" role="status"><CheckCircle2 size={17}/><span>{message}</span><button onClick={onClose} aria-label="Dismiss"><X size={15}/></button></div>}
export function formatDate(value:string|null|undefined){if(!value)return "Not available";const date=new Date(value);return Number.isNaN(date.valueOf())?value:new Intl.DateTimeFormat(undefined,{dateStyle:"medium",timeStyle:"short"}).format(date)}
export function formatBytes(bytes:number){if(bytes<1024)return `${bytes} B`;if(bytes<1024**2)return `${(bytes/1024).toFixed(1)} KB`;return `${(bytes/1024**2).toFixed(1)} MB`}

