import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity, AlertCircle, ArrowLeft, ArrowRight, Bell, CalendarDays,
  CheckCircle2, ChevronDown, ClipboardList, Clock3, Download, FileText,
  Globe2, Home, LogOut, MapPin, Menu, Package, QrCode, Search, Settings,
  ShieldCheck, ShoppingBag, Smartphone, Store, Ticket, TrendingUp, User,
  Users, X, Zap
} from "lucide-react";
import QRCode from "qrcode";
import "./styles.css";

const DEMO = {
  rural: { email: "rural@example.com", password: "demo123", role: "rural" },
  shop: { email: "shop@example.com", password: "demo123", role: "shop" },
  officer: { email: "officer@example.com", password: "demo123", role: "officer" }
};

const users = [
  { id: 1, name: "Rahul Patil", mobile: "9876543210", village: "Satnavari", status: "Verified" },
  { id: 2, name: "Sita Wankhede", mobile: "9823456712", village: "Satnavari", status: "Verified" },
  { id: 3, name: "Amit Meshram", mobile: "9812345678", village: "Koradi", status: "Pending" },
  { id: 4, name: "Pooja Borkar", mobile: "9898989898", village: "Kamptee", status: "Verified" },
  { id: 5, name: "Vijay Shende", mobile: "9765432109", village: "Hingna", status: "Verified" }
];

const initialBookings = [
  { id: "B001", user: "Rahul Patil", token: "SR-2026-00125", date: "2026-09-18", time: "10:30 AM", shop: "Satnavari Ration Shop", items: ["Rice 5 kg", "Wheat 5 kg", "Sugar 1 kg"], verification: "Verified", collection: "Pending", qr: "SRQR-8F4A92D7C31E" },
  { id: "B002", user: "Sita Wankhede", token: "SR-2026-00126", date: "2026-09-18", time: "10:35 AM", shop: "Satnavari Ration Shop", items: ["Rice 5 kg", "Sugar 1 kg"], verification: "Pending", collection: "Pending", qr: "SRQR-19BC42E9A7F1" },
  { id: "B003", user: "Amit Meshram", token: "SR-2026-00127", date: "2026-09-18", time: "10:40 AM", shop: "Koradi Ration Shop", items: ["Wheat 5 kg"], verification: "Verified", collection: "Completed", qr: "SRQR-2A77C0B19D44" },
  { id: "B004", user: "Pooja Borkar", token: "SR-2026-00128", date: "2026-09-18", time: "11:00 AM", shop: "Satnavari Ration Shop", items: ["Rice 5 kg"], verification: "Expired", collection: "Cancelled", qr: "SRQR-3D91AA7C11B2" }
];

const shops = [
  { id: "S01", name: "Satnavari Ration Shop", village: "Satnavari", beneficiaries: 1240, efficiency: 94, stock: "Healthy" },
  { id: "S02", name: "Koradi Ration Shop", village: "Koradi", beneficiaries: 980, efficiency: 91, stock: "Healthy" },
  { id: "S03", name: "Kamptee Ration Shop", village: "Kamptee", beneficiaries: 1560, efficiency: 87, stock: "Low Sugar" },
  { id: "S04", name: "Hingna Ration Shop", village: "Hingna", beneficiaries: 810, efficiency: 96, stock: "Healthy" }
];

function App() {
  const [session, setSession] = useState(null);
  const [loginRole, setLoginRole] = useState("rural");
  const [login, setLogin] = useState({ email: DEMO.rural.email, password: DEMO.rural.password });
  const [page, setPage] = useState("dashboard");
  const [history, setHistory] = useState(["dashboard"]);
  const [sidebar, setSidebar] = useState(true);
  const [toast, setToast] = useState(null);
  const [bookings, setBookings] = useState(initialBookings);
  const [selectedBooking, setSelectedBooking] = useState(initialBookings[0]);
  const [showQR, setShowQR] = useState(false);
  const [showScanner, setShowScanner] = useState(false);
  const [scannerResult, setScannerResult] = useState(null);
  const [language, setLanguage] = useState("English");
  const [search, setSearch] = useState("");

  const navigate = (next) => {
    setHistory(h => [...h, next]);
    setPage(next);
  };
  const back = () => {
    setHistory(h => {
      const next = h.length > 1 ? h.slice(0, -1) : ["dashboard"];
      setPage(next[next.length - 1]);
      return next;
    });
  };
  const notify = (message, type="success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const loginSubmit = (e) => {
    e.preventDefault();
    const expected = DEMO[loginRole];
    if (login.email.trim().toLowerCase() === expected.email && login.password === expected.password) {
      setSession({ role: loginRole, email: login.email });
      setPage("dashboard"); setHistory(["dashboard"]);
      notify("Secure login successful");
    } else {
      notify("Use the demo credentials shown below.", "error");
    }
  };

  const logout = () => { setSession(null); setPage("dashboard"); setHistory(["dashboard"]); };

  if (!session) return <LoginScreen role={loginRole} setRole={(r)=>{setLoginRole(r);setLogin({email:DEMO[r].email,password:DEMO[r].password})}} login={login} setLogin={setLogin} onSubmit={loginSubmit} language={language} setLanguage={setLanguage} />;

  const nav = {
    rural: [
      ["dashboard","Dashboard",Home],["generate","Generate Token",Ticket],["my-token","My Token & QR",QrCode],
      ["history","Collection History",ClipboardList],["feedback","Feedback",Activity]
    ],
    shop: [
      ["dashboard","Dashboard",Home],["queue","Today's Queue",Users],["scanner","QR Verification",QrCode],
      ["collections","Collections",CheckCircle2],["inventory","Inventory",Package],["reports","Reports",TrendingUp]
    ],
    officer: [
      ["dashboard","Dashboard",Home],["analytics","Analytics",TrendingUp],["shops","Shop Management",Store],
      ["beneficiaries","Beneficiaries",Users],["complaints","Complaints",AlertCircle],["policies","Policy Settings",Settings],
      ["audit","Audit Trail",ShieldCheck],["reports","Government Reports",FileText]
    ]
  }[session.role];

  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebar ? "open" : "closed"}`}>
        <div className="brand">
          <div className="brand-mark">SR</div>
          <div><strong>Smart Ration</strong><span>HSD2C Distribution Platform</span></div>
        </div>
        <div className="nav-section">MAIN MENU</div>
        {nav.map(([id,label,Icon]) => (
          <button key={id} className={`nav-item ${page===id ? "active":""}`} onClick={()=>navigate(id)}>
            <Icon size={19}/><span>{label}</span>
          </button>
        ))}
        <div className="sidebar-bottom">
          <div className="offline"><span className="online-dot"></span> System Online</div>
          <button className="nav-item" onClick={logout}><LogOut size={19}/><span>Sign out</span></button>
        </div>
      </aside>

      <main className={`main ${sidebar ? "with-sidebar" : ""}`}>
        <header className="topbar">
          <button className="icon-btn mobile-menu" onClick={()=>setSidebar(!sidebar)}><Menu/></button>
          <div className="top-search"><Search size={17}/><input placeholder="Search dashboard..." value={search} onChange={e=>setSearch(e.target.value)}/></div>
          <div className="top-actions">
            <button className="icon-btn"><Bell size={19}/><i></i></button>
            <div className="language"><Globe2 size={16}/><select value={language} onChange={e=>setLanguage(e.target.value)}><option>English</option><option>मराठी</option><option>हिन्दी</option></select></div>
            <div className="profile"><div className="avatar">{session.role[0].toUpperCase()}</div><div><strong>{session.role==="rural"?"Rural User":session.role==="shop"?"Shop Owner":"Government Official"}</strong><small>{session.email}</small></div><ChevronDown size={15}/></div>
          </div>
        </header>

        <div className="page-content">
          {history.length > 1 && <div className="breadcrumbs"><button onClick={back}><ArrowLeft size={15}/> Back</button><span>/</span><span>Dashboard</span><span>/</span><strong>{page.replace("-", " ")}</strong></div>}
          {page==="dashboard" && <Dashboard role={session.role} bookings={bookings} navigate={navigate} notify={notify} />}
          {page==="generate" && <GenerateToken onCreated={(b)=>{setBookings(x=>[b,...x]);setSelectedBooking(b);navigate("my-token");notify("Token and QR generated successfully")}} notify={notify}/>}
          {page==="my-token" && <MyToken booking={selectedBooking} onQR={()=>setShowQR(true)} />}
          {page==="history" && <History bookings={bookings} />}
          {page==="feedback" && <Feedback notify={notify}/>}
          {page==="queue" && <Queue bookings={bookings} search={search} onSelect={(b)=>{setSelectedBooking(b);navigate("scanner")}} />}
          {page==="scanner" && <ScannerPage onScan={(code)=>{const b=bookings.find(x=>x.qr===code);setScannerResult(b || {error:true,code});}} result={scannerResult} onComplete={(b)=>{setBookings(x=>x.map(y=>y.id===b.id?{...y,verification:"Verified",collection:"Completed"}:y));setScannerResult(null);notify("Collection completed and audit record created")}} />}
          {page==="collections" && <Collections bookings={bookings} setBookings={setBookings} notify={notify}/>}
          {page==="inventory" && <Inventory />}
          {page==="reports" && <Reports role={session.role}/>}
          {page==="analytics" && <Analytics />}
          {page==="shops" && <ShopManagement notify={notify}/>}
          {page==="beneficiaries" && <Beneficiaries />}
          {page==="complaints" && <Complaints notify={notify}/>}
          {page==="policies" && <Policies notify={notify}/>}
          {page==="audit" && <Audit />}
        </div>
      </main>

      {toast && <div className={`toast ${toast.type}`}><CheckCircle2 size={18}/>{toast.message}</div>}
      {showQR && <QRModal booking={selectedBooking} onClose={()=>setShowQR(false)}/>}
      {showScanner && <ScannerPage onScan={()=>{}} result={null} onComplete={()=>{}} compact onClose={()=>setShowScanner(false)}/>}
    </div>
  );
}

function LoginScreen({role,setRole,login,setLogin,onSubmit,language,setLanguage}) {
  const copy = {rural:["Rural User","Secure access for beneficiaries"],shop:["Shop Owner","Manage queue, inventory and collections"],officer:["Government Official","Monitor services and governance"]}[role];
  return <div className="login-page">
    <div className="login-art">
      <div className="login-brand"><div className="brand-mark light">SR</div><div><b>Smart Ration</b><small>HSD2C Distribution Platform</small></div></div>
      <div className="art-content">
        <span className="eyebrow">DIGITAL INDIA • SECURE • TRANSPARENT</span>
        <h1>Smart Ration <em>Distribution</em></h1>
        <p>Technology-driven ration distribution for a healthier and stronger community.</p>
        <div className="feature-pills"><span>🛡 Secure Access</span><span>👥 Fair Distribution</span><span>📊 Better Governance</span></div>
        <div className="grain-illustration"><div className="sack"></div><div className="bowl b1"></div><div className="bowl b2"></div><div className="bowl b3"></div></div>
      </div>
      <div className="art-footer">Ensuring Food Security<br/><b>for Every Family</b></div>
    </div>
    <div className="login-card-wrap">
      <div className="language login-lang"><Globe2 size={15}/><select value={language} onChange={e=>setLanguage(e.target.value)}><option>English</option><option>मराठी</option><option>हिन्दी</option></select></div>
      <form className="login-card" onSubmit={onSubmit}>
        <span className="eyebrow blue">PUBLIC SERVICE PLATFORM</span>
        <h2>Smart Ration Distribution</h2><p>Secure role-based access for rural users, ration shops and government officials.</p>
        <div className="role-tabs">{["rural","shop","officer"].map(r=><button type="button" key={r} className={role===r?"selected":""} onClick={()=>setRole(r)}>{r==="rural"?"👤 Rural User":r==="shop"?"🏪 Shop Owner":"🏛 Government Official"}</button>)}</div>
        <label>Email / Mobile Number<input value={login.email} onChange={e=>setLogin({...login,email:e.target.value})}/></label>
        <label>Password<input type="password" value={login.password} onChange={e=>setLogin({...login,password:e.target.value})}/></label>
        <div className="remember"><label><input type="checkbox" defaultChecked/> Remember me</label><a>Forgot password?</a></div>
        <button className="primary-btn" type="submit">Login securely <ArrowRight size={17}/></button>
        <div className="or"><span>OR</span></div>
        <div className="demo-box"><b>Demo Accounts:</b><br/>rural@example.com | shop@example.com | officer@example.com<br/><small>Password: demo123</small></div>
        <div className="login-trust"><ShieldCheck/> HSD2C Compliant <span/> 🔒 Data Encrypted <span/> 📶 Works Offline</div>
      </form>
    </div>
  </div>
}

function PageHeader({title,subtitle,action}) {
  return <div className="page-header"><div><div className="eyebrow blue">SMART RATION • HSD2C</div><h1>{title}</h1><p>{subtitle}</p></div>{action}</div>
}

function Dashboard({role,bookings,navigate,notify}) {
  const stats = role==="rural" ? [
    ["Current Token","SR-2026-00125","10:30 AM",Ticket,"blue"],
    ["Next Collection","Today","10:30 AM",Clock3,"cyan"],
    ["Ration Status","Ready","3 Items",Package,"green"],
    ["Shop Location","Satnavari","2.4 km",MapPin,"orange"]
  ] : role==="shop" ? [
    ["Today's Tokens","28","+12% today",Ticket,"blue"],["Completed","21","75% efficiency",CheckCircle2,"green"],
    ["Pending","7","Next: 10:35 AM",Clock3,"orange"],["Stock Health","Healthy","3 commodities",Package,"cyan"]
  ] : [
    ["Beneficiaries Served","4,590","+8.4% this month",Users,"blue"],["Tokens Generated","12,845","+14.2%",Ticket,"cyan"],
    ["Collection Efficiency","92.6%","+3.1%",TrendingUp,"green"],["Active Shops","48","4 regions",Store,"orange"]
  ];
  return <><PageHeader title={`${role==="rural"?"Welcome back":"Good afternoon"}`} subtitle={role==="rural"?"Manage your ration booking, token and collection details.":role==="shop"?"Monitor today's queue and complete ration distribution.":"Monitor ration distribution performance across your jurisdiction."}/>
  <div className="stats-grid">{stats.map(([a,b,c,I,cl])=><button className={`stat-card ${cl}`} key={a} onClick={()=>navigate(role==="rural"&&a==="Current Token"?"my-token":role==="shop"&&a==="Today's Tokens"?"queue":role==="officer"?"analytics":"inventory")}><div className="stat-top"><span>{a}</span><I size={19}/></div><strong>{b}</strong><small>{c}</small><ArrowRight className="stat-arrow" size={17}/></button>)}</div>
  {role==="rural" ? <RuralHome navigate={navigate}/> : role==="shop" ? <ShopHome bookings={bookings} navigate={navigate} notify={notify}/> : <OfficerHome navigate={navigate}/>}
</>
}

function RuralHome({navigate}) {
  return <div className="grid-2"><section className="panel hero-panel"><div className="panel-title"><div><span className="eyebrow blue">YOUR ACTIVE BOOKING</span><h2>Ration Collection Token</h2></div><span className="status success">● Confirmed</span></div><div className="token-big">SR-2026-00125</div><div className="booking-meta"><div><Clock3/><b>10:30 AM</b><small>Today, 18 Sep 2026</small></div><div><MapPin/><b>Satnavari Ration Shop</b><small>2.4 km away</small></div><div><Package/><b>3 Items</b><small>Rice • Wheat • Sugar</small></div></div><div className="actions"><button className="primary-btn" onClick={()=>navigate("my-token")}><QrCode/> View QR</button><button className="secondary-btn" onClick={()=>navigate("history")}><ClipboardList/> History</button></div></section><section className="panel"><div className="panel-title"><div><span className="eyebrow blue">QUICK ACTIONS</span><h2>What would you like to do?</h2></div></div><div className="quick-grid"><button onClick={()=>navigate("generate")}><Ticket/><b>Generate Token</b><small>Book your next collection</small></button><button onClick={()=>navigate("my-token")}><QrCode/><b>Show QR Code</b><small>Verify at the shop</small></button><button onClick={()=>navigate("history")}><ClipboardList/><b>Collection History</b><small>View previous visits</small></button><button onClick={()=>navigate("feedback")}><Activity/><b>Give Feedback</b><small>Rate your experience</small></button></div></section></div>
}

function ShopHome({bookings,navigate,notify}) {
  return <div className="grid-2"><section className="panel"><div className="panel-title"><div><span className="eyebrow blue">LIVE QUEUE</span><h2>Today's Arrivals</h2></div><button className="link-btn" onClick={()=>navigate("queue")}>View all <ArrowRight size={14}/></button></div><QueueTable bookings={bookings.slice(0,4)} onSelect={b=>{}}/></section><section className="panel"><div className="panel-title"><div><span className="eyebrow blue">FAST VERIFICATION</span><h2>QR Verification</h2></div></div><div className="scanner-card"><div className="scanner-icon"><QrCode size={40}/></div><h3>Verify a customer token</h3><p>Scan the customer's QR code to instantly verify their booking.</p><button className="primary-btn" onClick={()=>navigate("scanner")}><QrCode/> Open QR Scanner</button><button className="secondary-btn" onClick={()=>notify("Manual QR entry opened")}>Enter QR manually</button></div></section></div>
}

function OfficerHome({navigate}) {
  return <><div className="grid-2"><section className="panel"><div className="panel-title"><div><span className="eyebrow blue">DISTRIBUTION TREND</span><h2>Monthly Performance</h2></div><select className="small-select"><option>Last 6 months</option><option>This year</option></select></div><BarChart/></section><section className="panel"><div className="panel-title"><div><span className="eyebrow blue">SHOP PERFORMANCE</span><h2>Top Performing Shops</h2></div><button className="link-btn" onClick={()=>navigate("shops")}>Manage <ArrowRight size={14}/></button></div>{shops.map(s=><div className="shop-row" key={s.id}><div className="shop-avatar"><Store size={18}/></div><div className="grow"><b>{s.name}</b><small>{s.village} • {s.beneficiaries} beneficiaries</small></div><strong>{s.efficiency}%</strong></div>)}</section></div><div className="feature-grid"><button onClick={()=>navigate("analytics")}><TrendingUp/><b>Advanced Analytics</b><span>Regional trends, efficiency and token rates</span></button><button onClick={()=>navigate("audit")}><ShieldCheck/><b>Audit Trail</b><span>Transparent activity and security records</span></button><button onClick={()=>navigate("reports")}><FileText/><b>Government Reports</b><span>Export CSV, Excel and PDF-ready reports</span></button></div></>
}

function GenerateToken({onCreated,notify}) {
  const [step,setStep]=useState(1); const [items,setItems]=useState({rice:true,wheat:true,sugar:true}); const [date,setDate]=useState("2026-09-18"); const [time,setTime]=useState("10:30 AM"); const [shop,setShop]=useState("Satnavari Ration Shop");
  const slots=["10:00 AM","10:05 AM","10:10 AM","10:15 AM","10:20 AM","10:25 AM","10:30 AM","10:35 AM","10:40 AM","10:45 AM","10:50 AM","10:55 AM","11:00 AM"];
  const create=()=>{const b={id:"B"+Date.now(),user:"Demo Rural User",token:"SR-2026-"+String(Math.floor(10000+Math.random()*89999)),date,time,shop,items:Object.entries(items).filter(([,v])=>v).map(([k])=>k==="rice"?"Rice 5 kg":k==="wheat"?"Wheat 5 kg":"Sugar 1 kg"),verification:"Pending",collection:"Pending",qr:"SRQR-"+Math.random().toString(16).slice(2,14).toUpperCase()};onCreated(b)};
  return <><PageHeader title="Generate Ration Token" subtitle="Select your ration items and reserve a suitable 5-minute collection slot."/><div className="stepper">{["Select Items","Choose Slot","Confirm"].map((x,i)=><div className={step===i+1?"current":step>i+1?"done":""} key={x}><span>{step>i+1?"✓":i+1}</span>{x}</div>)}</div>{step===1&&<section className="panel form-panel"><h2>Select ration items</h2><p className="muted">Choose the items you want to collect. Vernacular names are shown for accessibility.</p><div className="item-grid">{[["rice","Rice","Tandul","5 kg","🌾"],["wheat","Wheat","Gahu","5 kg","🌾"],["sugar","Sugar","Sakhar","1 kg","◉"]].map(([k,n,v,q,icon])=><button className={`item-card ${items[k]?"chosen":""}`} onClick={()=>setItems({...items,[k]:!items[k]})} key={k}><span className="item-icon">{icon}</span><div><b>{n} <small>({v})</small></b><span>{q} standard quota</span></div>{items[k]&&<CheckCircle2 className="check"/>}</button>)}</div><button className="primary-btn wide" onClick={()=>setStep(2)}>Continue to Time Slot <ArrowRight/></button></section>}{step===2&&<section className="panel form-panel"><h2>Choose collection slot</h2><div className="form-grid"><label>Ration Shop<select value={shop} onChange={e=>setShop(e.target.value)}><option>Satnavari Ration Shop</option><option>Koradi Ration Shop</option></select></label><label>Date<input type="date" value={date} onChange={e=>setDate(e.target.value)}/></label></div><div className="slot-grid">{slots.map((s,i)=><button key={s} className={time===s?"slot selected":"slot"} onClick={()=>setTime(s)}><Clock3 size={15}/>{s}<small>{i%4===0?"8 seats":"Available"}</small></button>)}</div><div className="actions"><button className="secondary-btn" onClick={()=>setStep(1)}><ArrowLeft/> Back</button><button className="primary-btn" onClick={()=>setStep(3)}>Review Booking <ArrowRight/></button></div></section>}{step===3&&<section className="panel confirmation"><div className="success-circle"><CheckCircle2 size={42}/></div><h2>Review & Confirm</h2><p className="muted">Your token will be generated after confirmation.</p><div className="summary"><div><span>Shop</span><b>{shop}</b></div><div><span>Date & Time</span><b>{date} • {time}</b></div><div><span>Items</span><b>{Object.entries(items).filter(([,v])=>v).map(([k])=>k==="rice"?"Rice 5 kg":k==="wheat"?"Wheat 5 kg":"Sugar 1 kg").join(" • ")}</b></div></div><div className="actions"><button className="secondary-btn" onClick={()=>setStep(2)}><ArrowLeft/> Change</button><button className="primary-btn" onClick={create}><CheckCircle2/> Confirm & Generate Token</button></div></section>}</>
}

function MyToken({booking,onQR}) {
  if(!booking) return <EmptyState title="No active token" text="Generate a token to see your QR verification code."/>
  return <><PageHeader title="My Token & QR" subtitle="Keep this QR code ready when you arrive at your ration shop." action={<span className="status success">● Active</span>}/><div className="token-layout"><section className="panel token-card"><span className="eyebrow blue">YOUR TOKEN NUMBER</span><div className="token-number">{booking.token}</div><div className="qr-preview"><QRCodeCanvas value={booking.qr}/></div><b className="qr-ref">{booking.qr}</b><button className="primary-btn wide" onClick={onQR}><QrCode/> Show Full QR</button><button className="secondary-btn wide" onClick={()=>window.print()}><Download/> Print / Save</button></section><section className="panel"><span className="eyebrow blue">BOOKING DETAILS</span><h2>Collection appointment</h2><div className="detail-list"><div><Clock3/><span>Date & Time<b>{booking.date} • {booking.time}</b></span></div><div><MapPin/><span>Ration Shop<b>{booking.shop}</b></span></div><div><Package/><span>Pre-selected items<b>{booking.items.join(" • ")}</b></span></div><div><Smartphone/><span>Notification<b>SMS / Email confirmation simulated</b></span></div></div><div className="info-callout"><ShieldCheck/><div><b>Secure verification</b><p>Your QR contains a non-sensitive reference only. Identity and booking validation happen through the secure system.</p></div></div></section></div></>
}

function QRCodeCanvas({value,size=190}) {
  const ref=React.useRef(null);
  React.useEffect(()=>{if(ref.current) QRCode.toCanvas(ref.current,value,{width:size,margin:2,errorCorrectionLevel:"H"});},[value,size]);
  return <canvas ref={ref} aria-label="Ration token QR code"/>;
}

function QRModal({booking,onClose}) {
  return <div className="modal-backdrop"><div className="modal qr-modal"><button className="modal-close" onClick={onClose}><X/></button><span className="eyebrow blue">SMART RATION VERIFICATION</span><h2>Ration QR Code</h2><p className="muted">{booking?.token}</p><div className="modal-qr">{booking&&<QRCodeCanvas value={booking.qr} size={280}/>}</div><b>{booking?.qr}</b><div className="qr-valid">● Active • Valid for scheduled collection window</div><button className="primary-btn wide" onClick={()=>window.print()}><Download/> Print / Save QR</button></div></div>
}

function Queue({bookings,search,onSelect}) {
  const data=bookings.filter(b=>(b.user+b.token+b.time).toLowerCase().includes(search.toLowerCase()));
  return <><PageHeader title="Today's Queue" subtitle="Live customer arrivals and pre-selected ration requirements."/><section className="panel"><div className="table-toolbar"><div><b>{data.length} customers</b><span className="muted"> • Real-time queue</span></div><div className="toolbar-actions"><button className="secondary-btn"><Download/> Export</button></div></div><QueueTable bookings={data} onSelect={onSelect}/></section></>
}

function QueueTable({bookings,onSelect}) {
  return <div className="table-wrap"><table><thead><tr><th>User</th><th>Token</th><th>Arrival</th><th>Ration</th><th>Verification</th><th>Collection</th><th></th></tr></thead><tbody>{bookings.map(b=><tr key={b.id}><td><div className="user-cell"><div className="mini-avatar">{b.user[0]}</div><b>{b.user}</b></div></td><td><code>{b.token}</code></td><td>{b.time}</td><td>{b.items.join(", ")}</td><td><span className={`status ${b.verification==="Verified"?"success":b.verification==="Expired"?"danger":"warning"}`}>{b.verification}</span></td><td><span className={`status ${b.collection==="Completed"?"success":b.collection==="Cancelled"?"danger":"warning"}`}>{b.collection}</span></td><td><button className="icon-btn" onClick={()=>onSelect?.(b)}><ArrowRight size={16}/></button></td></tr>)}</tbody></table></div>
}

function ScannerPage({onScan,result,onComplete,compact,onClose}) {
  const [manual,setManual]=useState(""); const [message,setMessage]=useState("");
  const verify=(code)=>{setMessage("Verifying...");setTimeout(()=>{onScan(code);setMessage("Verification completed");},400)};
  return <section className={`scanner-page ${compact?"compact":""}`}>{onClose&&<button className="modal-close" onClick={onClose}><X/></button>}<PageHeader title="QR Verification" subtitle="Scan the customer's Smart Ration token or enter its reference manually."/><div className="scanner-layout"><section className="panel"><div className="scanner-frame"><QrCode size={48}/><div className="scan-corners"></div><p>Camera scanner</p><small>Point the camera at the QR code</small></div><button className="primary-btn wide" onClick={()=>verify("SRQR-8F4A92D7C31E")}><QrCode/> Start Camera Scanner</button><div className="or"><span>OR</span></div><label>Enter QR reference<input placeholder="SRQR-..." value={manual} onChange={e=>setManual(e.target.value)}/></label><button className="secondary-btn wide" disabled={!manual} onClick={()=>verify(manual)}>Verify manually</button><p className="muted small">{message}</p></section><section className="panel">{result?.error?<div className="result error"><AlertCircle size={48}/><h2>QR verification failed</h2><p>Invalid, expired, revoked or unrecognized QR reference.</p><code>{result.code}</code></div>:result?<div className="result success-result"><div className="success-circle"><CheckCircle2 size={42}/></div><h2>Customer Verified</h2><p>Token and booking are valid for this shop.</p><div className="summary"><div><span>Customer</span><b>{result.user}</b></div><div><span>Token</span><b>{result.token}</b></div><div><span>Arrival</span><b>{result.time}</b></div><div><span>Ration</span><b>{result.items.join(" • ")}</b></div></div>{result.collection!=="Completed"&&<button className="primary-btn wide" onClick={()=>onComplete(result)}><CheckCircle2/> Mark Collection Complete</button>}</div>:<EmptyState title="Ready to verify" text="Scan a QR code to display customer and ration details here."/>}</section></div></section>
}

function Collections({bookings,setBookings,notify}) {
  const complete=(id)=>{setBookings(x=>x.map(b=>b.id===id?{...b,collection:"Completed",verification:"Verified"}:b));notify("Collection marked completed")};
  return <><PageHeader title="Collections" subtitle="Verify and complete today's ration distributions."/><section className="panel"><QueueTable bookings={bookings} onSelect={()=>{}}/><div className="collection-actions">{bookings.filter(b=>b.collection==="Pending").map(b=><button key={b.id} className="secondary-btn" onClick={()=>complete(b.id)}>Complete {b.token}</button>)}</div></section></>
}

function Inventory() {
  const rows=[["Rice (Tandul)","1,850 kg","2,400 kg","77%","Healthy"],["Wheat (Gahu)","1,420 kg","2,000 kg","71%","Healthy"],["Sugar (Sakhar)","620 kg","1,000 kg","62%","Monitor"]];
  return <><PageHeader title="Inventory" subtitle="Track stock against pre-selected customer ration requirements."/><div className="stats-grid">{[["Rice","1,850 kg"],["Wheat","1,420 kg"],["Sugar","620 kg"],["Allocated Today","186 kg"]].map(([x,y],i)=><div className="stat-card blue" key={x}><div className="stat-top"><span>{x}</span><Package size={19}/></div><strong>{y}</strong><small>Available stock</small></div>)}</div><section className="panel"><h2>Commodity inventory</h2><div className="table-wrap"><table><thead><tr><th>Commodity</th><th>Available</th><th>Capacity</th><th>Utilization</th><th>Status</th></tr></thead><tbody>{rows.map(r=><tr key={r[0]}>{r.map((v,i)=><td key={i}>{i===4?<span className={`status ${v==="Healthy"?"success":"warning"}`}>{v}</span>:v}</td>)}</tr>)}</tbody></table></div></section></>
}

function Reports({role}) {
  return <><PageHeader title={role==="officer"?"Government Reports":"Reports"} subtitle="Download operational and distribution reports with filters." action={<button className="primary-btn" onClick={()=>alert("Report export simulated. Connect backend export service for production files.")}><Download/> Export Report</button>}/><div className="report-grid">{["Daily Collection Report","Token Generation Report","Inventory Allocation","Shop Performance","QR Verification Report","Audit Activity Report"].map((x,i)=><button className="report-card" key={x}><FileText/><div><b>{x}</b><small>CSV • Excel • PDF-ready</small></div><Download size={17}/></button>)}</div></>
}

function Analytics() {
  return <><PageHeader title="Government Analytics" subtitle="Aggregated distribution intelligence across the jurisdiction."/><div className="stats-grid">{[["Beneficiaries Served","4,590","+8.4%"],["Token Rate","12,845","+14.2%"],["Collection Efficiency","92.6%","+3.1%"],["QR Success Rate","97.8%","+1.8%"]].map(x=><div className="stat-card blue" key={x[0]}><div className="stat-top"><span>{x[0]}</span><TrendingUp size={19}/></div><strong>{x[1]}</strong><small>{x[2]} vs previous period</small></div>)}</div><div className="grid-2"><section className="panel"><div className="panel-title"><div><span className="eyebrow blue">TREND ANALYSIS</span><h2>Tokens & Collections</h2></div></div><BarChart/></section><section className="panel"><div className="panel-title"><div><span className="eyebrow blue">REGIONAL DISTRIBUTION</span><h2>Beneficiaries by area</h2></div></div>{["Satnavari","Koradi","Kamptee","Hingna"].map((x,i)=><div className="progress-row" key={x}><span>{x}</span><div><i style={{width:`${92-i*9}%`}}></i></div><b>{[1240,980,1560,810][i]}</b></div>)}</section></div></>
}

function BarChart() {
  const vals=[48,62,55,71,68,84,78,92,86,96,88,100];
  return <div className="chart"><div className="chart-bars">{vals.map((v,i)=><div className="bar-col" key={i}><div className="bar" style={{height:`${v}%`}}></div><small>{["Oct","Nov","Dec","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep"][i]}</small></div>)}</div></div>
}

function ShopManagement({notify}) { return <><PageHeader title="Shop Management" subtitle="Manage ration shops and authorized operators." action={<button className="primary-btn" onClick={()=>notify("Add shop workflow opened")}>+ Add Shop</button>}/><section className="panel"><div className="table-wrap"><table><thead><tr><th>Shop</th><th>Village</th><th>Beneficiaries</th><th>Efficiency</th><th>Stock</th><th>Action</th></tr></thead><tbody>{shops.map(s=><tr key={s.id}><td><b>{s.name}</b></td><td>{s.village}</td><td>{s.beneficiaries}</td><td>{s.efficiency}%</td><td><span className={`status ${s.stock==="Healthy"?"success":"warning"}`}>{s.stock}</span></td><td><button className="secondary-btn">Manage</button></td></tr>)}</tbody></table></div></section></> }

function Beneficiaries() { return <><PageHeader title="Beneficiaries" subtitle="Search and review registered rural users."/><section className="panel"><div className="table-wrap"><table><thead><tr><th>Name</th><th>Mobile</th><th>Village</th><th>Identity</th></tr></thead><tbody>{users.map(u=><tr key={u.id}><td><div className="user-cell"><div className="mini-avatar">{u.name[0]}</div><b>{u.name}</b></div></td><td>{u.mobile}</td><td>{u.village}</td><td><span className={`status ${u.status==="Verified"?"success":"warning"}`}>{u.status}</span></td></tr>)}</tbody></table></div></section></> }

function Complaints({notify}) { const [text,setText]=useState(""); return <><PageHeader title="Complaints & Feedback" subtitle="Monitor citizen feedback and grievance resolution."/><div className="grid-2"><section className="panel"><h2>Open complaints</h2>{["Queue delay at Kamptee shop","SMS reminder not received","Inventory availability query"].map((x,i)=><div className="complaint" key={x}><AlertCircle/><div><b>{x}</b><small>Reported {i+1} day(s) ago • Priority {i===0?"High":"Normal"}</small></div><button className="secondary-btn" onClick={()=>notify("Complaint marked for review")}>Review</button></div>)}</section><section className="panel form-panel"><h2>Resolution note</h2><textarea value={text} onChange={e=>setText(e.target.value)} placeholder="Enter action taken..."></textarea><button className="primary-btn" onClick={()=>{setText("");notify("Resolution saved to audit trail")}}>Save Resolution</button></section></div></> }

function Policies({notify}) { const [slot,setSlot]=useState(5); const [qr,setQr]=useState(30); return <><PageHeader title="Policy Configuration" subtitle="Configure quotas, slot duration and verification policy."/><section className="panel settings-form"><label>Time slot duration (minutes)<select value={slot} onChange={e=>setSlot(e.target.value)}><option>5</option><option>10</option><option>15</option></select></label><label>QR validity after slot (minutes)<select value={qr} onChange={e=>setQr(e.target.value)}><option>15</option><option>30</option><option>45</option></select></label><label>Identity verification required<select><option>Yes</option><option>No</option></select></label><label>SMS reminders<select><option>Enabled</option><option>Disabled</option></select></label><button className="primary-btn" onClick={()=>notify("Policy configuration saved")}>Save Policy</button></section></> }

function Audit() { const logs=[["09:42","QR_VERIFICATION","Shop Owner","SUCCESS","SRQR-8F4A92D7C31E"],["09:41","COLLECTION_COMPLETED","Shop Owner","SUCCESS","SR-2026-00124"],["09:35","TOKEN_GENERATED","Rural User","SUCCESS","SR-2026-00125"],["09:21","LOGIN","Government Official","SUCCESS","officer@example.com"],["09:12","QR_VERIFICATION","Shop Owner","REJECTED","SRQR-INVALID"]]; return <><PageHeader title="Audit Trail" subtitle="Transparent record of authentication, QR and distribution activity."/><section className="panel"><div className="table-wrap"><table><thead><tr><th>Time</th><th>Event</th><th>Actor</th><th>Result</th><th>Reference</th></tr></thead><tbody>{logs.map((r,i)=><tr key={i}>{r.map((v,j)=><td key={j}>{j===3?<span className={`status ${v==="SUCCESS"?"success":"danger"}`}>{v}</span>:v}</td>)}</tr>)}</tbody></table></div></section></> }

function History({bookings}) { return <><PageHeader title="Collection History" subtitle="Your previous ration token and collection records."/><section className="panel"><QueueTable bookings={bookings.filter(b=>b.collection==="Completed")} onSelect={()=>{}}/></section></> }
function Feedback({notify}) { const [rating,setRating]=useState(5); const [comment,setComment]=useState(""); return <section className="center-panel"><div className="panel feedback-card"><span className="eyebrow blue">SERVICE QUALITY</span><h1>How was your ration collection?</h1><p className="muted">Your feedback helps improve service for every family.</p><div className="stars">{[1,2,3,4,5].map(n=><button className={n<=rating?"on":""} onClick={()=>setRating(n)} key={n}>★</button>)}</div><textarea value={comment} onChange={e=>setComment(e.target.value)} placeholder="Tell us about your experience..."></textarea><button className="primary-btn" onClick={()=>{setComment("");notify("Thank you. Feedback recorded.")}}>Submit Feedback</button></div></section> }
function EmptyState({title,text}) { return <div className="empty"><ClipboardList size={42}/><h2>{title}</h2><p>{text}</p></div> }

createRoot(document.getElementById("root")).render(<App/>);