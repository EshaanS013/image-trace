import { ArrowLeft, LockKeyhole, Moon, Sun } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "../components";
import { useWorkspace } from "../state";

export function SettingsPage(){const {theme,toggleTheme}=useWorkspace();return <div className="public-page"><header className="public-header"><Link className="brand" to="/cases"><div className="brand-mark">IT</div><div><strong>IMAGE TRACE</strong><span>Local investigation workspace</span></div></Link></header><div className="form-wrap"><Link className="back-link" to="/cases"><ArrowLeft size={15}/>Back to cases</Link><p className="eyebrow">SETTINGS</p><h1>Workspace preferences</h1><section className="settings-card"><div><h2>Appearance</h2><p>Theme is stored only on this device.</p></div><Button variant="secondary" onClick={toggleTheme} icon={theme==="dark"?Sun:Moon}>Use {theme==="dark"?"light":"dark"} theme</Button></section><section className="settings-card"><div><h2>Map privacy</h2><p>Online tiles are disabled. Evidence coordinates remain inside the local application.</p></div><LockKeyhole/></section><section className="responsible-card"><h2>Responsible use</h2><p>Use synthetic or consented evidence. IMAGE TRACE provides qualified indicators, not definitive claims about authenticity, intent, identity, or conduct.</p></section></div></div>}

