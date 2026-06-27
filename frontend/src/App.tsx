// Copyright © 2026 Andrew Wolverton. All Rights Reserved.

import React, { useEffect, useMemo, useState } from "react";




function copyCloseKitText(label: string, copyText: string) {
  navigator.clipboard
    .writeText(copyText)
    .then(() => {
      const status = document.getElementById("close-kit-status");

      if (!status) return;

      status.textContent = `Copied ${label}!`;
      status.removeAttribute("hidden");

      window.setTimeout(() => {
        status.setAttribute("hidden", "true");
        status.textContent = "";
      }, 1400);
    })
    .catch(() => {
      window.alert("Copy failed. Please try again.");
    });
}

const LOCK_SHOW_DEMO_PASSWORD =
  String(import.meta.env.VITE_SHOW_DEMO_PASSWORD || "").toLowerCase() === "true" &&
  String(import.meta.env.VITE_OWNER_DEMO_PASSWORD || "").trim().length > 0;

const LOCK_OWNER_DEMO_PASSWORD = String(import.meta.env.VITE_OWNER_DEMO_PASSWORD || "").trim();

const LOCK_OWNER_EMAIL = "awolf4277@gmail.com";
const LOCK_CONTACT_SUBJECT = encodeURIComponent("I AM THE ONE™ SaaS Demo Inquiry");
const LOCK_CONTACT_BODY = encodeURIComponent(`Hi Andrew,

I saw the I AM THE ONE™ SaaS demo and I am interested in talking about a build.

Name:
Business:
Package interested in:
Budget:
Timeline:
What I need:
`);

const LOCK_MAILTO_HREF = `mailto:${LOCK_OWNER_EMAIL}?subject=${LOCK_CONTACT_SUBJECT}&body=${LOCK_CONTACT_BODY}`;

const LOCK_GMAIL_HREF = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(
  LOCK_OWNER_EMAIL
)}&su=${LOCK_CONTACT_SUBJECT}&body=${LOCK_CONTACT_BODY}`;

const CLOVER_STARTER_DEPOSIT_LINK = String(import.meta.env.VITE_CLOVER_STARTER_DEPOSIT_LINK || "");
const CLOVER_STARTER_FULL_LINK = String(import.meta.env.VITE_CLOVER_STARTER_FULL_LINK || "");
const CLOVER_PRO_DEPOSIT_LINK = String(import.meta.env.VITE_CLOVER_PRO_DEPOSIT_LINK || "");



type ApiHealth = {
  ok?: boolean;
  app?: string;
  brand?: string;
  system?: string;
  owner?: string;
  version?: string;
  timestamp?: string;
  ts?: string;
  counts?: {
    stores?: number;
    products?: number;
    orders?: number;
  };
};

type AnalyticsSummary = {
  ok?: boolean;
  total_visits?: number;
  visits_today?: number;
  landing_visits?: number;
  store_visits?: number;
  owner_visits?: number;
  setup_request_submits?: number;
  demo_pitch_copies?: number;
  conversion_rate?: number;
};

type AnalyticsEventName =
  | "landing_page_visit"
  | "store_visit"
  | "owner_visit"
  | "setup_request_submit"
  | "demo_pitch_copy";

type Store = {
  id?: string;
  slug?: string;
  name?: string;
  brand?: string;
  system?: string;
  owner_name?: string;
  status?: string;
  plan?: string;
  currency?: string;
  product_count?: number;
};

type Product = {
  id?: string;
  store_slug?: string;
  store_id?: string;
  store_name?: string;
  sku?: string;
  name?: string;
  category?: string;
  description?: string;
  price_cents?: number;
  stock?: number;
  image_url?: string;
  is_active?: number;
};

type Order = {
  id?: string;
  store_slug?: string;
  store_name?: string;
  buyer_name?: string;
  buyer_email?: string;
  buyer_phone?: string;
  notes?: string;
  status?: string;
  payment_status?: string;
  subtotal_cents?: number;
  tax_cents?: number;
  shipping_cents?: number;
  total_cents?: number;
  currency?: string;
  created_at?: string;
  item_count?: number;
};

type SetupRequest = {
  id?: string;
  name?: string;
  business_name?: string;
  email?: string;
  phone?: string;
  what_i_sell?: string;
  budget_range?: string;
  timeline?: string;
  website?: string;
  message?: string;
  source?: string;
  status?: string;
  created_at?: string;
};

type CartLine = {
  product_id: string;
  sku: string;
  name: string;
  price_cents: number;
  qty: number;
  stock: number;
};

type BuyerInfo = {
  name: string;
  email: string;
  phone: string;
  notes: string;
};

type ProductForm = {
  store_slug: string;
  sku: string;
  name: string;
  category: string;
  description: string;
  price_cents: string;
  stock: string;
  image_url: string;
};

type LoadState = "booting" | "ready" | "error";

const DEFAULT_API_BASE = "https://i-am-the-one-saas-api.onrender.com";

function cleanApiBase(raw: unknown) {
  const value = String(raw || "")
    .trim()
    .replace(/^VITE_BACKEND_URL\s*=\s*/i, "")
    .replace(/^Value:\s*/i, "")
    .replace(/^["']|["']$/g, "")
    .replace(/\/+$/, "");

  if (!value) return DEFAULT_API_BASE;

  try {
    const parsed = new URL(value);
    return parsed.origin;
  } catch {
    return DEFAULT_API_BASE;
  }
}

const RENDER_API_BASE = "https://i-am-the-one-saas-api.onrender.com";

function productionSafeApiBase() {
  const raw = cleanApiBase((import.meta as any).env?.VITE_BACKEND_URL);

  if (typeof window !== "undefined") {
    const host = window.location.hostname;

    if (
      host.includes("i-am-the-one-saas-frontend-live.onrender.com") &&
      (!raw || raw.includes("127.0.0.1") || raw.includes("localhost"))
    ) {
      return RENDER_API_BASE;
    }
  }

  return raw || RENDER_API_BASE;
}

const API_BASE = productionSafeApiBase();

function apiUrl(path: string) {
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${cleanPath}`;
}

function getStoreSlug() {
  const parts = window.location.pathname.split("/").filter(Boolean);

  if (parts[0] === "store" && parts[1]) return parts[1];

  return "demo";
}

function money(cents?: number) {
  const safe = Number.isFinite(Number(cents)) ? Number(cents) : 0;

  return (safe / 100).toLocaleString(undefined, {
    style: "currency",
    currency: "USD"
  });
}

function dateLabel(value?: string) {
  if (!value) return "—";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString();
}

function normalizeProducts(payload: any): Product[] {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.products)) return payload.products;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.inventory)) return payload.inventory;
  if (Array.isArray(payload?.data)) return payload.data;

  return [];
}

function normalizeStores(payload: any): Store[] {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.stores)) return payload.stores;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.data)) return payload.data;

  return [];
}

function normalizeOrders(payload: any): Order[] {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.orders)) return payload.orders;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.data)) return payload.data;

  return [];
}

function displayLeadBudget(request: SetupRequest) {
  const business = (request.business_name || "").toLowerCase();
  const budget = request.budget_range || "";

  if (business.includes("blue ridge") && budget.includes("500")) return "$1,500+ Pro";
  if (business.includes("summit clean") && budget.includes("starter")) return "$499+ Starter";
  if (business.includes("crown cut") && (budget === "-" || budget.includes("499"))) return "$299-$499";

  return budget || "Budget TBD";
}

function isHotLead(request: SetupRequest) {
  const combined = `${displayLeadBudget(request)} ${request.timeline || ""}`.toLowerCase();

  return combined.includes("1500") || combined.includes("this week");
}

function normalizeSetupRequests(payload: any): SetupRequest[] {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.setup_requests)) return payload.setup_requests;
  if (Array.isArray(payload?.requests)) return payload.requests;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.data)) return payload.data;

  return [];
}

function productKey(product: Product, index: number) {
  return String(product.id || product.sku || `product-${index}`);
}

function assetUrl(value?: string | null) {
  const raw = String(value || "").trim();

  if (!raw) return "";

  if (raw.startsWith("http://") || raw.startsWith("https://") || raw.startsWith("data:")) {
    return raw;
  }

  if (raw.startsWith("/products/")) {
    return raw;
  }

  if (raw.startsWith("/")) {
    return raw;
  }

  return `/${raw}`;
}


async function apiJson<T>(
  path: string,
  options: RequestInit = {},
  token = ""
): Promise<T> {
  const hasBody = Boolean(options.body);
  const headers = new Headers(options.headers || {});

  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  if (hasBody && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const url = apiUrl(path);

  const response = await fetch(url, {
    ...options,
    headers
  });

  const text = await response.text();
  let payload: any = {};

  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = { raw: text };
    }
  }

  if (!response.ok) {
    const message =
      payload?.message ||
      payload?.error ||
      payload?.raw ||
      `${response.status} ${response.statusText}`;

    throw new Error(String(message));
  }

  return payload as T;
}

async function trackAnalyticsEvent(event_name: AnalyticsEventName, path = "") {
  try {
    await apiJson<any>("/api/analytics/event", {
      method: "POST",
      body: JSON.stringify({
        event_name,
        path:
          path ||
          (typeof window !== "undefined"
            ? `${window.location.pathname}${window.location.hash}`
            : ""),
        source: "frontend"
      })
    });
  } catch {
    // Analytics should never block the storefront or owner console.
  }
}

function App() {
  const readRoutePath = () => {
    const rawRoute = window.location.hash
      ? window.location.hash.replace(/^#/, "")
      : window.location.pathname;

    return rawRoute.startsWith("/") ? rawRoute : `/${rawRoute}`;
  };

  const [path, setPath] = useState(readRoutePath);

  useEffect(() => {
    const syncRoute = () => setPath(readRoutePath());

    window.addEventListener("hashchange", syncRoute);
    window.addEventListener("popstate", syncRoute);

    return () => {
      window.removeEventListener("hashchange", syncRoute);
      window.removeEventListener("popstate", syncRoute);
    };
  }, []);

  const pathParts = path.split("/").filter(Boolean);
  const storeSlug = pathParts[0] === "store" && pathParts[1] ? pathParts[1] : getStoreSlug();

  const isOwner = path.startsWith("/owner");
  const isStore = path.startsWith("/store");

  const [health, setHealth] = useState<ApiHealth | null>(null);
  const [stores, setStores] = useState<Store[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [setupRequests, setSetupRequests] = useState<SetupRequest[]>([]);

  const [copiedCloseKit, setCopiedCloseKit] = useState("");

  const copyCloseKit = async (label: string, text: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedCloseKit(label);
    window.setTimeout(() => setCopiedCloseKit(""), 1400);
  };

  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [ownerProducts, setOwnerProducts] = useState<Product[]>([]);

  const [selectedIndex, setSelectedIndex] = useState(0);
  const [cart, setCart] = useState<CartLine[]>([]);
  const [buyer, setBuyer] = useState<BuyerInfo>({
    name: "",
    email: "",
    phone: "",
    notes: ""
  });

  const [ownerPassword, setOwnerPassword] = useState("");
  const [ownerToken, setOwnerToken] = useState(() => {
    return localStorage.getItem("wolf_owner_token") || "";
  });

  const [loadState, setLoadState] = useState<LoadState>("booting");
  const [ownerLoading, setOwnerLoading] = useState(false);
  const [checkingOut, setCheckingOut] = useState(false);

  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [lastOrder, setLastOrder] = useState<Order | null>(null);

  const selectedProduct = products[selectedIndex] || products[0] || null;
  const selectedImage = assetUrl(selectedProduct?.image_url);

  const cartTotal = useMemo(() => {
    return cart.reduce((sum, line) => sum + line.price_cents * line.qty, 0);
  }, [cart]);

  const cartCount = useMemo(() => {
    return cart.reduce((sum, line) => sum + line.qty, 0);
  }, [cart]);

  async function bootStorefront() {
    setLoadState("booting");
    setError("");

    try {
      const [healthData, storesData, productData] = await Promise.all([
        apiJson<ApiHealth>("/api/health").catch(() => null),
        apiJson<any>("/api/stores").catch(() => ({ stores: [] })),
        apiJson<any>(`/api/stores/${storeSlug}/products`)
      ]);

      const normalizedProducts = normalizeProducts(productData);

      setHealth(healthData);
      setStores(normalizeStores(storesData));
      setProducts(normalizedProducts);

      if (selectedIndex >= normalizedProducts.length) {
        setSelectedIndex(0);
      }

      setLoadState("ready");
    } catch (err: any) {
      setError(err?.message || "Unable to load storefront.");
      setLoadState("error");
    }
  }

  async function loadOwnerData(token = ownerToken) {
    if (!token) return;

    setOwnerLoading(true);
    setError("");

    try {
      const ordersData = await apiJson<any>("/api/owner/orders", {}, token);
      setOrders(normalizeOrders(ordersData));

      const setupRequestsData = await apiJson<any>("/api/owner/setup-requests", {}, token).catch(() => ({
        setup_requests: []
      }));
      setSetupRequests(normalizeSetupRequests(setupRequestsData));

      const analyticsData = await apiJson<AnalyticsSummary>("/api/owner/analytics", {}, token).catch(() => null);
      setAnalytics(analyticsData);

      const productsData = await apiJson<any>("/api/owner/products", {}, token).catch(() => ({
        products: []
      }));

      const storesData = await apiJson<any>("/api/stores").catch(() => ({
        stores: []
      }));

      const healthData = await apiJson<ApiHealth>("/api/health").catch(() => null);

      setOwnerProducts(normalizeProducts(productsData));
      setStores(normalizeStores(storesData));
      setHealth(healthData);
    } catch (err: any) {
      setError(err?.message || "Unable to load owner orders.");

      if (String(err?.message || "").includes("OWNER_AUTH_REQUIRED")) {
        logoutOwner();
      }
    } finally {
      setOwnerLoading(false);
    }
  }

  useEffect(() => {
    bootStorefront();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storeSlug]);

  useEffect(() => {
    const eventName: AnalyticsEventName = isOwner
      ? "owner_visit"
      : isStore
        ? "store_visit"
        : "landing_page_visit";

    trackAnalyticsEvent(eventName, path);
  }, [path, isOwner, isStore]);

  useEffect(() => {
    if (ownerToken) {
      loadOwnerData(ownerToken);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ownerToken]);

  function addToCart(product: Product, index: number) {
    const product_id = String(product.id || "");
    const sku = String(product.sku || "");
    const name = product.name || sku || `Product ${index + 1}`;
    const stock = Math.max(0, Number(product.stock || 0));
    const price = Number(product.price_cents || 0);

    if (!product_id && !sku) {
      setNotice("This product is missing an ID/SKU.");
      return;
    }

    if (stock <= 0) {
      setNotice(`${name} is out of stock.`);
      return;
    }

    setCart((previous) => {
      const found = previous.find((line) => {
        return line.product_id === product_id || line.sku === sku;
      });

      if (found) {
        if (found.qty >= stock) {
          setNotice(`Stock limit reached for ${name}.`);
          return previous;
        }

        setNotice(`${name} quantity updated.`);

        return previous.map((line) => {
          if (line.product_id === found.product_id && line.sku === found.sku) {
            return { ...line, qty: line.qty + 1 };
          }

          return line;
        });
      }

      setNotice(`${name} added to cart.`);

      return [
        ...previous,
        {
          product_id,
          sku,
          name,
          price_cents: price,
          qty: 1,
          stock
        }
      ];
    });
  }

  function removeFromCart(product_id: string, sku: string) {
    setCart((previous) => {
      return previous.filter((line) => {
        return !(line.product_id === product_id && line.sku === sku);
      });
    });

    setNotice("Cart updated.");
  }

  function updateBuyer(field: keyof BuyerInfo, value: string) {
    setBuyer((previous) => ({ ...previous, [field]: value }));
  }

  async function submitCheckout() {
    if (!cart.length) {
      setNotice("Cart is empty.");
      return;
    }

    if (!buyer.name.trim() || !buyer.email.trim()) {
      setNotice("Name and email are required before checkout.");
      return;
    }

    setCheckingOut(true);
    setError("");

    try {
      const payload = await apiJson<any>(`/api/stores/${storeSlug}/checkout`, {
        method: "POST",
        body: JSON.stringify({
          buyer,
          items: cart.map((line) => ({
            product_id: line.product_id,
            sku: line.sku,
            qty: line.qty
          }))
        })
      });

      setLastOrder(payload.order || null);
      setCart([]);
      setBuyer({
        name: "",
        email: "",
        phone: "",
        notes: ""
      });

      if (Array.isArray(payload.updated_products)) {
        setProducts(payload.updated_products);
      } else {
        await bootStorefront();
      }

      if (ownerToken) {
        await loadOwnerData(ownerToken);
      }

      setNotice(`Order created: ${payload?.order?.id || "success"}`);
    } catch (err: any) {
      setError(err?.message || "Checkout failed.");
    } finally {
      setCheckingOut(false);
    }
  }

  async function loginOwner(event: React.FormEvent) {
    event.preventDefault();

    setOwnerLoading(true);
    setError("");

    try {
      const payload = await apiJson<any>("/api/owner/login", {
        method: "POST",
        body: JSON.stringify({
          password: ownerPassword
        })
      });

      const token = String(payload.token || "");

      if (!token) {
        throw new Error("Owner login returned no token.");
      }

      localStorage.setItem("wolf_owner_token", token);
      setOwnerToken(token);
      setOwnerPassword("");
      setNotice("Owner console unlocked.");

      await loadOwnerData(token);
    } catch (err: any) {
      setError(err?.message || "Owner login failed.");
    } finally {
      setOwnerLoading(false);
    }
  }

  function logoutOwner() {
    localStorage.removeItem("wolf_owner_token");
    setOwnerToken("");
    setOrders([]);
    setSetupRequests([]);
    setAnalytics(null);
    setOwnerProducts([]);
    setNotice("Owner console locked.");
  }

  async function createOwnerProduct(form: ProductForm) {
    if (!ownerToken) {
      setError("Owner token required.");
      return;
    }

    const slug = form.store_slug.trim() || "demo";

    try {
      await apiJson<any>(
        `/api/stores/${slug}/products`,
        {
          method: "POST",
          body: JSON.stringify({
            sku: form.sku,
            name: form.name,
            category: form.category,
            description: form.description,
            price_cents: Number(form.price_cents || 0),
            stock: Number(form.stock || 0),
            image_url: form.image_url
          })
        },
        ownerToken
      );

      setNotice("Product created.");
      await bootStorefront();
      await loadOwnerData(ownerToken);
    } catch (err: any) {
      setError(err?.message || "Product create failed.");
    }
  }

  async function updateProductStock(product: Product, nextStock: number) {
    if (!ownerToken) {
      setError("Owner token required.");
      return;
    }

    const slug = product.store_slug || storeSlug;
    const id = product.id;

    if (!id) {
      setError("Product ID missing.");
      return;
    }

    try {
      await apiJson<any>(
        `/api/stores/${slug}/products/${id}`,
        {
          method: "PUT",
          body: JSON.stringify({
            stock: Math.max(0, nextStock)
          })
        },
        ownerToken
      );

      setNotice("Stock updated.");
      await bootStorefront();
      await loadOwnerData(ownerToken);
    } catch (err: any) {
      setError(err?.message || "Stock update failed.");
    }
  }

  return (
    <main className="v3-app">
      <OwnershipBar
        health={health}
        storeSlug={storeSlug}
        cartCount={cartCount}
        onRefresh={() => {
          bootStorefront();

          if (ownerToken) {
            loadOwnerData(ownerToken);
          }
        }}
      />

      {notice ? <div className="v3-toast">{notice}</div> : null}

      {error ? (
        <section className="v3-alert">
          <strong>System message</strong>
          <span>{error}</span>
        </section>
      ) : null}

      {isOwner ? (
        ownerToken ? (
          <OwnerConsole
            health={health}
            stores={stores}
            orders={orders}
            setupRequests={setupRequests}
            analytics={analytics}
            products={ownerProducts}
            loading={ownerLoading}
            onRefresh={() => loadOwnerData(ownerToken)}
            onLogout={logoutOwner}
            onCreateProduct={createOwnerProduct}
            onUpdateStock={updateProductStock}
          />
        ) : (
          <OwnerGate
            password={ownerPassword}
            setPassword={setOwnerPassword}
            loading={ownerLoading}
            onSubmit={loginOwner}
          />
        )
      ) : isStore ? (
        <CustomerStorefront
          storeSlug={storeSlug}
          health={health}
          products={products}
          selectedIndex={selectedIndex}
          selectedProduct={selectedProduct}
          selectedImage={selectedImage}
          loadState={loadState}
          cart={cart}
          buyer={buyer}
          cartTotal={cartTotal}
          checkingOut={checkingOut}
          lastOrder={lastOrder}
          onSelectProduct={setSelectedIndex}
          onAdd={addToCart}
          onRemove={removeFromCart}
          onBuyerChange={updateBuyer}
          onCheckout={submitCheckout}
          onClearCart={() => setCart([])}
        />
      ) : (
        <SaasLanding health={health} products={products} stores={stores} />
      )}

      <footer className="v3-footer">
        <span>I AM THE ONE™</span>
        <span>WOLF OS™</span>
        <span>Copyright © 2026 Andrew Wolverton. All Rights Reserved.</span>
      </footer>
    </main>
  );
}

function OwnershipBar({
  health,
  storeSlug,
  cartCount,
  onRefresh
}: {
  health: ApiHealth | null;
  storeSlug: string;
  cartCount: number;
  onRefresh: () => void;
}) {
  return (
    <header className="ownership-bar">
      <a className="brand-lockup" href="/">
        <span className="wolf-mark">W</span>
        <span>
          <strong>I AM THE ONE™</strong>
          <small>WOLF OS™ SaaS v3</small>
        </span>
      </a>

      <nav className="v3-nav">
        <a href="/#store/demo">Customer Store</a>
        <a href="/#owner">Owner Console</a>
      </nav>

      <div className="system-strip">
        <span className={health?.ok ? "status-dot online" : "status-dot"} />
        <span>{health?.ok ? "ONLINE" : "CHECKING"}</span>
        <span className="hide-mobile">STORE: {storeSlug.toUpperCase()}</span>
        <span>CART: {cartCount}</span>
        <button className="mini-button" onClick={onRefresh}>
          Refresh
        </button>
      </div>
    </header>
  );
}

function SaasLanding({
  health,
  products,
  stores
}: {
  health: ApiHealth | null;
  products: Product[];
  stores: Store[];
}) {
  const productCount = products.length || health?.counts?.products || 0;
  const storeCount = stores.length || health?.counts?.stores || 1;
  const orderCount = health?.counts?.orders || 0;
  const featuredProduct = products[0];

  return (
    <section className="landing-grid">
      <div className="landing-hero">
        <p className="v3-kicker">I AM THE ONE™ · WOLF OS™ SaaS</p>
        <h1>Turn your business into a live storefront with checkout, products, orders, and an owner dashboard ready to run.</h1>
        <p>
          I AM THE ONE™ gives creators, small brands, and service businesses a
          buyer-ready commerce system they can demo today, customize fast, and
          deploy without starting from zero.
        </p>

        <div className="landing-actions">
          <a className="v3-button primary" href="/#store/demo">
            View Live Store Demo
          </a>
          <a className="v3-button secondary" href="/#owner">
            Open Owner Console
          </a>
        </div>

        <div className="shine-box">
          <p className="eyebrow">Owner Console Demo</p>

              {LOCK_SHOW_DEMO_PASSWORD ? (
                <>
                  <p>
                    <strong>Owner URL:</strong> /#owner
                  </p>
                  <p>
                    <strong>Password:</strong> {LOCK_OWNER_DEMO_PASSWORD}
                  </p>
                  <p>
                    <strong>Mode:</strong> Local demo access enabled
                  </p>
                </>
              ) : (
                <>
                  <p>
                    Owner console access is available by request for serious buyers, client demos, and setup discussions.
                  </p>
                  <div className="cta-row">
                    <a className="primary-btn" href={LOCK_GMAIL_HREF} target="_blank" rel="noreferrer">
                      Request Owner Demo Access
                    </a>
                    <a className="secondary-btn" href={LOCK_MAILTO_HREF}>
                      Email Andrew
                    </a>
                  </div>
                </>
              )}
        </div>
      </div>

      <aside className="landing-panel">
        <p className="v3-kicker">Live System Status</p>
        <h2>{health?.ok ? "Online and taking orders" : "Checking backend"}</h2>

        <div className="metric-list">
          <Metric label="Stores" value={storeCount} />
          <Metric label="Products" value={productCount} />
          <Metric label="Orders" value={orderCount} />
        </div>

        <div className="shine-box">
          <strong>Featured demo product</strong>
          <span>{featuredProduct?.name || "Wolf Signature Hoodie"}</span>
          <span>{money(featuredProduct?.price_cents || 9900)}</span>
          <span>{Number(featuredProduct?.stock || 0)} live stock</span>
        </div>
      </aside>

      <aside className="landing-panel">
        <p className="v3-kicker">Hire Andrew / Launch Packages</p>
        <h2>Turn a small business into a live storefront + owner dashboard.</h2>
        <p>
          Built by Andrew Wolverton. I AM THE ONE™ / WOLF OS™ gives businesses a
          branded buying flow, buyer lead capture, and a simple command center
          instead of starting from zero.
        </p>

        <div className="metric-list">
          <Metric label="Starter Storefront" value="$499+" />
          <Metric label="Pro Storefront + Dashboard" value="$1,500+" />
          <Metric label="Custom SaaS Buildout" value="$3,000+" />
        </div>

        <div className="shine-box">
          <strong>Best fit</strong>
          <span>Clothing brands, barbers, beauty studios, pressure washing, cleaning, food trucks, and local service businesses.</span>
          <span>Use the live demo to pick a package, request setup, and start with a real system foundation.</span>
        </div>

        <SetupRequestForm />

        <PaymentOptions />

        <PremiumBuyerProof />

        <BuyerConversionPolish />

        <div className="shine-box">
          <strong>What buyers get</strong>
          <span>Mobile-ready storefront demo</span>
          <span>Owner dashboard for orders and products</span>
          <span>Real checkout flow with manual payment mode</span>
          <span>Deploy-ready frontend and backend foundation</span>
        </div>

        <div className="shine-box">
          <strong>Demo Close Kit</strong>
          <span>
            Copy a ready-to-send pitch for buyers, then open the live store or
            owner console during a demo.
          </span>

          <div className="landing-actions">
            <button
              className="v3-button primary"
              type="button"
              onClick={() => {
                const origin = window.location.origin;

                navigator.clipboard.writeText(
                  `I built a live storefront + owner dashboard demo for small brands, creators, and service businesses.

It includes:
- Customer storefront
- Product catalog
- Cart and checkout
- Owner console
- Orders
- Inventory controls
- Buyer lead capture

Live Store Demo: ${origin}/#store/demo
Owner Console Demo: ${origin}/#owner

If you want something like this customized for your business, I can help set it up.`
                );

                trackAnalyticsEvent("demo_pitch_copy", window.location.pathname + window.location.hash);

                alert("Demo pitch copied.");
              }}
            >
              Copy Demo Pitch
            </button>

            <a className="v3-button secondary" href="/#store/demo">
              Store Demo
            </a>

            <a className="v3-button secondary" href="/#owner">
              Owner Console
            </a>
          </div>
        </div>

        <div className="landing-actions">
          <a className="v3-button primary" href="/#store/demo">
            Start Demo
          </a>
          <button
            type="button"
            className="v3-button secondary"
            onClick={() => {
              document.getElementById("request-setup-form")?.scrollIntoView({
                behavior: "smooth",
                block: "start",
              });
            }}
          >
            Request Setup
          </button>
        </div>
      </aside>
    </section>
  );
}


function CustomerStorefront({
  storeSlug,
  health,
  products,
  selectedIndex,
  selectedProduct,
  selectedImage,
  loadState,
  cart,
  buyer,
  cartTotal,
  checkingOut,
  lastOrder,
  onSelectProduct,
  onAdd,
  onRemove,
  onBuyerChange,
  onCheckout,
  onClearCart
}: {
  storeSlug: string;
  health: ApiHealth | null;
  products: Product[];
  selectedIndex: number;
  selectedProduct: Product | null;
  selectedImage: string;
  loadState: LoadState;
  cart: CartLine[];
  buyer: BuyerInfo;
  cartTotal: number;
  checkingOut: boolean;
  lastOrder: Order | null;
  onSelectProduct: (index: number) => void;
  onAdd: (product: Product, index: number) => void;
  onRemove: (product_id: string, sku: string) => void;
  onBuyerChange: (field: keyof BuyerInfo, value: string) => void;
  onCheckout: () => void;
  onClearCart: () => void;
}) {
  return (
    <section className="customer-layout">
      <aside className="catalog-rail">
        <div className="rail-heading">
          <p className="v3-kicker">Live Catalog</p>
          <h2>{storeSlug.toUpperCase()}</h2>
        </div>

        {loadState === "booting" ? (
          <div className="ghost-card">Loading premium inventory...</div>
        ) : products.length ? (
          <div className="product-list">
            {products.map((product, index) => (
              <button
                className={index === selectedIndex ? "product-row active" : "product-row"}
                key={productKey(product, index)}
                onClick={() => onSelectProduct(index)}
              >
                <span className="row-index">{String(index + 1).padStart(2, "0")}</span>
                <span>
                  <strong>{product.name || product.sku || `Product ${index + 1}`}</strong>
                  <small>
                    {product.category || "Premium"} · {money(product.price_cents)} ·{" "}
                    {Number(product.stock || 0)} stock
                  </small>
                </span>
              </button>
            ))}
          </div>
        ) : (
          <div className="ghost-card">No products returned yet.</div>
        )}
      </aside>

      <section className="v3-product-stage">
        <div className="stage-top">
          <div>
            <p className="v3-kicker">Customer Experience</p>
            <h1>{selectedProduct?.name || "I AM THE ONE™ Storefront"}</h1>
          </div>

          <span className={health?.ok ? "v3-pill online" : "v3-pill"}>
            {health?.ok ? "LIVE API" : "API CHECK"}
          </span>
        </div>

        <div className="product-showcase">
          <div className="hero-media-card">
            {selectedImage ? (
              <img src={selectedImage} alt={selectedProduct?.name || "Product"} />
            ) : (
              <div className="fallback-product-mark">
                {(selectedProduct?.sku || selectedProduct?.name || "IATO")
                  .slice(0, 4)
                  .toUpperCase()}
              </div>
            )}

            <div className="media-badge">Real API · Live Inventory</div>
          </div>

          <div className="product-info-card">
            <p className="v3-kicker">{selectedProduct?.category || "Premium Item"}</p>
            <h2>{selectedProduct?.name || "Luxury Commerce Item"}</h2>
            <p>
              {selectedProduct?.description ||
                "Real product loaded from the SaaS backend."}
            </p>

            <div className="price-stock-row">
              <strong>{money(selectedProduct?.price_cents)}</strong>
              <span>{Number(selectedProduct?.stock || 0)} in stock</span>
            </div>

            <button
              className="v3-button primary full"
              disabled={!selectedProduct || Number(selectedProduct?.stock || 0) <= 0}
              onClick={() => selectedProduct && onAdd(selectedProduct, selectedIndex)}
            >
              Add to Cart
            </button>

            <div className="spec-grid">
              <span>
                <small>SKU</small>
                <strong>{selectedProduct?.sku || "—"}</strong>
              </span>
              <span>
                <small>Store</small>
                <strong>{storeSlug.toUpperCase()}</strong>
              </span>
              <span>
                <small>Mode</small>
                <strong>REAL</strong>
              </span>
            </div>
          </div>
        </div>
      </section>

      <aside className="checkout-panel">
        <div className="checkout-heading">
          <p className="v3-kicker">Real Checkout</p>
          <button onClick={onClearCart}>Clear</button>
        </div>

        <h2>Cart</h2>

        {cart.length ? (
          <div className="cart-stack">
            {cart.map((line) => (
              <div className="cart-item" key={`${line.product_id}-${line.sku}`}>
                <div>
                  <strong>{line.name}</strong>
                  <small>
                    {line.sku} · Qty {line.qty} · {money(line.price_cents)}
                  </small>
                </div>

                <button onClick={() => onRemove(line.product_id, line.sku)}>Remove</button>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-cart">No items in cart yet.</div>
        )}

        <div className="buyer-box">
          <p className="v3-kicker">Customer Info</p>

          <input
            placeholder="Full name *"
            value={buyer.name}
            onChange={(event) => onBuyerChange("name", event.target.value)}
          />

          <input
            placeholder="Email *"
            value={buyer.email}
            onChange={(event) => onBuyerChange("email", event.target.value)}
          />

          <input
            placeholder="Phone"
            value={buyer.phone}
            onChange={(event) => onBuyerChange("phone", event.target.value)}
          />

          <input
            placeholder="Order notes"
            value={buyer.notes}
            onChange={(event) => onBuyerChange("notes", event.target.value)}
          />
        </div>

        <div className="checkout-total">
          <span>Total</span>
          <strong>{money(cartTotal)}</strong>
        </div>

        <button
          className="v3-button primary full"
          disabled={!cart.length || checkingOut}
          onClick={onCheckout}
        >
          {checkingOut ? "Creating Order..." : "Create Real Order"}
        </button>

        {lastOrder ? (
          <div className="checkout-success-card">
            <div className="success-badge">ORDER CREATED</div>

            <h3>Order Created</h3>

            <p>
              This order is saved in WOLF OS™ and visible in the Owner Console.
            </p>

            <div className="success-grid">
              <span>Order ID</span>
              <strong>{lastOrder.id || "Generated"}</strong>

              <span>Buyer</span>
              <strong>{lastOrder.buyer_name || "Customer"}</strong>

              <span>Email</span>
              <strong>{lastOrder.buyer_email || "On file"}</strong>

              <span>Total</span>
              <strong>{money(lastOrder.total_cents)}</strong>

              <span>Payment</span>
              <strong>{lastOrder.payment_status || "manual / unpaid"}</strong>
            </div>

            <div className="payment-instructions">
              <strong>Manual payment mode</strong>
              <span>
                Send payment instructions to the buyer, then mark the order paid from
                the owner workflow later.
              </span>
            </div>

            <button
              className="v3-button secondary full"
              onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
            >
              Back to Store
            </button>
          </div>
        ) : (
          <small className="checkout-note">
            Creates a real SQLite order and decrements stock.
          </small>
        )}
      </aside>
    </section>
  );
}

function OwnerGate({
  password,
  setPassword,
  loading,
  onSubmit
}: {
  password: string;
  setPassword: (value: string) => void;
  loading: boolean;
  onSubmit: (event: React.FormEvent) => void;
}) {
  return (
    <section className="owner-gate">
      <div className="gate-card">
        <p className="v3-kicker">WOLF OS™ Owner Login</p>
        <h1>Real owner access.</h1>
        <p>
          This login posts to <code>/api/owner/login</code> and receives a real
          owner token from the Flask backend.
        </p>

        <form onSubmit={onSubmit}>
          <input
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Owner password"
            type="password"
          />

          <button className="v3-button primary" type="submit" disabled={loading}>
            {loading ? "Unlocking..." : "Unlock Console"}
          </button>
        </form>

        <small>Owner passwords:  or WOLF-DEMO</small>
      </div>
    </section>
  );
}


function PremiumBuyerProof() {
  return (
    <>
      <div className="shine-box">
        <strong>Why this is different</strong>
        <span>
          This is not a static website pitch. The demo already runs with a live API,
          products, orders, buyer leads, owner login, payment-ready setup, and a
          dashboard workflow a business can understand immediately.
        </span>
        <span>
          Your build starts from a working system foundation, then gets customized
          around your brand, offers, customer flow, and payment/deposit process.
        </span>
      </div>

      <div className="metric-list">
        <Metric label="Starter Deposit" value="$250" />
        <Metric label="Starter Delivery" value="3-7 days" />
        <Metric label="Revision Round" value="1 included" />
      </div>

      <div className="shine-box">
        <strong>How a client build works</strong>
        <span>1. Submit the setup request with your business details.</span>
        <span>2. Pick Starter, Pro, or Custom based on what you need.</span>
        <span>3. Pay the deposit to lock the build.</span>
        <span>4. Andrew customizes the storefront, offers, dashboard flow, and launch copy.</span>
        <span>5. You receive a live link you can show customers.</span>
      </div>

      <div className="shine-box">
        <strong>Scope clarity</strong>
        <span>
          Starter is for getting live fast. Deeper dashboards, payment integrations,
          automations, custom admin tools, and advanced workflows move into Pro or
          Custom pricing.
        </span>
        <span>
          This keeps the build clean, protects the timeline, and makes sure every
          client gets the right package instead of an endless cheap custom project.
        </span>
      </div>

      <div className="shine-box">
        <strong>Buyer FAQ</strong>
        <span><strong>Do I need products?</strong> No. Services, packages, bookings, quote requests, and digital offers work too.</span>
        <span><strong>Can this use Clover?</strong> Yes. Start with secure Clover payment links, then upgrade to deeper checkout later.</span>
        <span><strong>Is this custom?</strong> The foundation is already built. Your version gets customized around your brand and business flow.</span>
        <span><strong>Do I own my business content?</strong> Yes. Your brand, offers, copy, and customer-facing content are yours.</span>
      </div>
    </>
  );
}

function BuyerConversionPolish() {
  const scrollToSetup = () => {
    document.getElementById("request-setup-form")?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  return (
    <>
      <div className="shine-box">
        <strong>What happens after deposit?</strong>
        <span>1. Andrew confirms your business details, offers, and launch goal.</span>
        <span>2. Your services, products, or packages are added to the storefront.</span>
        <span>3. The page copy, buyer flow, and call-to-action are customized.</span>
        <span>4. Your setup request, quote, or payment/deposit path is connected.</span>
        <span>5. You receive a live link you can show customers.</span>
        <span>6. One revision round is included for Starter builds.</span>
      </div>

      <div className="shine-box">
        <strong>Starter package boundaries</strong>
        <span>Starter is designed to get a business live fast with a clean, buyer-ready foundation.</span>
        <span>Starter includes a branded storefront, offer/service cards, setup/request flow, live link, and one revision round.</span>
        <span>
          Starter does not include custom payment API integration, advanced booking logic,
          unlimited revisions, multi-user accounts, complex automations, or custom database workflows.
        </span>
        <span>Those upgrades are available in Pro or Custom packages.</span>
      </div>

      <div className="shine-box">
        <strong>Examples by business type</strong>
        <span><strong>Barbers:</strong> haircut packages, beard trims, VIP grooming, booking interest, and local lead capture.</span>
        <span><strong>Cleaners:</strong> house cleaning, pressure washing, driveway cleaning, quote requests, and service packages.</span>
        <span><strong>Clothing brands:</strong> hoodies, tees, merch bundles, product cards, orders, and inventory-ready structure.</span>
        <span><strong>Food trucks:</strong> menu items, catering requests, pickup interest, events, and contact flow.</span>
        <span><strong>Creators:</strong> digital products, service packages, launch offers, and buyer inquiry capture.</span>
      </div>

      <div className="shine-box">
        <strong>Client intake checklist</strong>
        <span>Business name and contact info</span>
        <span>Logo, colors, photos, and brand style if available</span>
        <span>Services, products, prices, or package offers</span>
        <span>Preferred payment/deposit method, including Clover link if available</span>
        <span>Website, social links, and launch deadline</span>
        <span>Deposit status before custom work begins</span>
      </div>

      <div className="shine-box premium-cta-box">
        <strong>Ready to start?</strong>
        <span>
          Submit the setup form, pick a package, and Andrew will confirm the next
          step before any custom work begins.
        </span>
        <div className="landing-actions payment-actions">
          <button type="button" className="v3-button primary" onClick={scrollToSetup}>
            Request Setup
          </button>
          <a className="v3-button secondary" href="/#store/demo">
            View Store Demo
          </a>
          <a className="v3-button secondary" href="/#owner">
            Open Owner Console
          </a>
        </div>
      </div>
    </>
  );
}

function PaymentOptions() {
  const scrollToSetup = () => {
    document.getElementById("request-setup-form")?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  const hasAnyCloverLink =
    CLOVER_STARTER_DEPOSIT_LINK || CLOVER_STARTER_FULL_LINK || CLOVER_PRO_DEPOSIT_LINK;

  return (
    <div className="shine-box payment-options-box">
      <strong>Payment Options</strong>
      <span>
        Clover-ready checkout path. Start with a setup request, then pay a deposit
        or package invoice through a secure Clover payment link.
      </span>

      <div className="landing-actions payment-actions">
        {CLOVER_STARTER_DEPOSIT_LINK ? (
          <a
            className="v3-button primary"
            href={CLOVER_STARTER_DEPOSIT_LINK}
            target="_blank"
            rel="noreferrer"
          >
            Pay Starter Deposit
          </a>
        ) : (
          <button type="button" className="v3-button primary" onClick={scrollToSetup}>
            Request Starter Deposit Link
          </button>
        )}

        {CLOVER_STARTER_FULL_LINK ? (
          <a
            className="v3-button secondary"
            href={CLOVER_STARTER_FULL_LINK}
            target="_blank"
            rel="noreferrer"
          >
            Pay Starter $499
          </a>
        ) : null}

        {CLOVER_PRO_DEPOSIT_LINK ? (
          <a
            className="v3-button secondary"
            href={CLOVER_PRO_DEPOSIT_LINK}
            target="_blank"
            rel="noreferrer"
          >
            Pay Pro Deposit
          </a>
        ) : null}
      </div>

      {!hasAnyCloverLink ? (
        <span>
          No Clover link is public yet. Submit the setup form and Andrew can send
          the correct deposit link for your package.
        </span>
      ) : null}
    </div>
  );
}

function SetupRequestForm() {
  const [form, setForm] = useState({
    name: "",
    business_name: "",
    email: "",
    phone: "",
    what_i_sell: "",
    budget_range: "",
    timeline: "",
    website: "",
    message: ""
  });

  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState("");
  const [formError, setFormError] = useState("");

  function updateField(field: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submitSetupRequest(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSent("");
    setFormError("");

    const name = form.name.trim();
    const email = form.email.trim();
    const whatISell = form.what_i_sell.trim();

    if (!name || !email || !whatISell) {
      setFormError("Name, email, and what you sell are required.");
      return;
    }

    try {
      setSubmitting(true);

      await apiJson<any>("/api/setup-requests", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          name,
          email,
          what_i_sell: whatISell,
          source: "homepage_setup_form"
        })
      });

      await trackAnalyticsEvent("setup_request_submit", window.location.pathname + window.location.hash);

      setSent("Request received. Andrew can review it in the Owner Console.");
      setForm({
        name: "",
        business_name: "",
        email: "",
        phone: "",
        what_i_sell: "",
        budget_range: "",
        timeline: "",
        website: "",
        message: ""
      });
    } catch (err: any) {
      setFormError(err?.message || "Setup request failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form id="request-setup-form" className="setup-form" onSubmit={submitSetupRequest}>
      <div className="setup-form-head">
        <p className="v3-kicker">Request Setup</p>
        <h3>Tell Andrew what you want to launch</h3>
        <p>
          Submit your business details and the request will appear inside the
          Owner Console as a real lead.
        </p>
      </div>

      <div className="setup-form-grid">
        <label>
          Name *
          <input
            value={form.name}
            onChange={(event) => updateField("name", event.target.value)}
            placeholder="Your name"
          />
        </label>

        <label>
          Business
          <input
            value={form.business_name}
            onChange={(event) => updateField("business_name", event.target.value)}
            placeholder="Business or brand name"
          />
        </label>

        <label>
          Email *
          <input
            type="email"
            value={form.email}
            onChange={(event) => updateField("email", event.target.value)}
            placeholder="you@example.com"
          />
        </label>

        <label>
          Phone
          <input
            value={form.phone}
            onChange={(event) => updateField("phone", event.target.value)}
            placeholder="Optional"
          />
        </label>

        <label>
          What do you sell? *
          <input
            value={form.what_i_sell}
            onChange={(event) => updateField("what_i_sell", event.target.value)}
            placeholder="Clothing, services, digital products..."
          />
        </label>

        <label>
          Budget range
          <select
            value={form.budget_range}
            onChange={(event) => updateField("budget_range", event.target.value)}
          >
            <option value="">Select range</option>
            <option value="$499+ Starter">$499+ Starter</option>
            <option value="$1,500+ Pro">$1,500+ Pro</option>
            <option value="$3,000+ Custom">$3,000+ Custom</option>
            <option value="Not sure yet">Not sure yet</option>
          </select>
        </label>

        <label>
          Timeline
          <select
            value={form.timeline}
            onChange={(event) => updateField("timeline", event.target.value)}
          >
            <option value="">Select timeline</option>
            <option value="ASAP">ASAP</option>
            <option value="This week">This week</option>
            <option value="This month">This month</option>
            <option value="Exploring">Exploring</option>
          </select>
        </label>

        <label>
          Website/social
          <input
            value={form.website}
            onChange={(event) => updateField("website", event.target.value)}
            placeholder="Link if you have one"
          />
        </label>
      </div>

      <label className="setup-message">
        Message
        <textarea
          value={form.message}
          onChange={(event) => updateField("message", event.target.value)}
          placeholder="Tell me what you want the storefront or SaaS system to do."
          rows={4}
        />
      </label>

      {formError ? <p className="form-error">{formError}</p> : null}
      {sent ? <p className="form-success">{sent}</p> : null}

      <button className="v3-button" type="submit" disabled={submitting}>
        {submitting ? "Sending..." : "Send Setup Request"}
      </button>
    </form>
  );
}


function OwnerConsole({
  health,
  stores,
  orders,
  setupRequests,
  analytics,
  products,
  loading,
  onRefresh,
  onLogout,
  onCreateProduct,
  onUpdateStock
}: {
  health: ApiHealth | null;
  stores: Store[];
  orders: Order[];
  setupRequests: SetupRequest[];
  analytics: AnalyticsSummary | null;
  products: Product[];
  loading: boolean;
  onRefresh: () => void;
  onLogout: () => void;
  onCreateProduct: (form: ProductForm) => Promise<void>;
  onUpdateStock: (product: Product, nextStock: number) => Promise<void>;
}) {
  const [form, setForm] = useState<ProductForm>({
    store_slug: "demo",
    sku: "",
    name: "",
    category: "Premium",
    description: "",
    price_cents: "",
    stock: "",
    image_url: ""
  });

  const inventoryValue = products.reduce((sum, product) => {
    return sum + Number(product.price_cents || 0) * Number(product.stock || 0);
  }, 0);

  const lowStock = products.filter((product) => {
    return Number(product.stock || 0) <= 3;
  }).length;

  async function submitProduct(event: React.FormEvent) {
    event.preventDefault();

    await onCreateProduct(form);

    setForm({
      store_slug: "demo",
      sku: "",
      name: "",
      category: "Premium",
      description: "",
      price_cents: "",
      stock: "",
      image_url: ""
    });
  }

  function setField(field: keyof ProductForm, value: string) {
    setForm((previous) => ({ ...previous, [field]: value }));
  }

  return (
    <section id="owner-console" className="owner-console">
      <div className="owner-hero">
        <div>
          <p className="v3-kicker">Operator Mode</p>
          <h1>WOLF OS™ SaaS Command Center</h1>
          <p>
            Real owner dashboard connected to orders, products, stores, inventory,
            and backend health.
          </p>

          <div className="demo-ready-strip">
            <span className="demo-ready-dot" />
            <strong>DEMO READY</strong>
            <span>Sales tools active · Leads loaded · Close Kit ready</span>
          </div>

          <p id="pitch-mode-note" className="pitch-mode-note" hidden>
            Pitch Mode is showing the clean sales view: checklist, close kit, leads, orders, and proof.
          </p>
        </div>

        <div className="owner-actions">
          <button
            type="button"
            className="v3-button secondary"
            onClick={(event) => {
              const consoleEl = document.getElementById("owner-console");
              const note = document.getElementById("pitch-mode-note");
              const enabled = consoleEl?.classList.toggle("pitch-mode") ?? false;

              if (note) note.hidden = !enabled;

              event.currentTarget.textContent = enabled ? "Full Console" : "Pitch Mode";
              event.currentTarget.classList.toggle("primary", enabled);
              event.currentTarget.classList.toggle("secondary", !enabled);
            }}
          >
            Pitch Mode
          </button>

          <button className="v3-button secondary" onClick={onRefresh} disabled={loading}>
            {loading ? "Refreshing..." : "Refresh"}
          </button>

          <button className="v3-button danger" onClick={onLogout}>
            Lock
          </button>
        </div>
      </div>

      <div className="metric-grid">
        <Metric label="API" value={health?.ok ? "Online" : "Check"} />
        <Metric label="Stores" value={stores.length || health?.counts?.stores || 0} />
        <Metric label="Products" value={products.length || health?.counts?.products || 0} />
        <Metric label="Orders" value={orders.length || health?.counts?.orders || 0} />
        <Metric label="Low Stock" value={lowStock} />
        <Metric label="Inventory Value" value={money(inventoryValue)} />
        <Metric label="Visits Today" value={analytics?.visits_today ?? 0} />
        <Metric label="Total Visits" value={analytics?.total_visits ?? 0} />
        <Metric label="Lead Rate" value={`${analytics?.conversion_rate ?? 0}%`} />
      </div>

      <div className="owner-panels">
        <div className="owner-panel wide launch-checklist-panel">
          <div className="panel-heading">
            <div>
              <p className="v3-kicker">Launch Checklist</p>
              <h2>Ready to Pitch</h2>
            </div>

            <span className="v3-pill online">LIVE</span>
          </div>

          <div className="launch-checklist-grid">
            <div className="launch-check-item">
              <span className="launch-check-icon">✓</span>
              <div>
                <strong>Live API connected</strong>
                <span>Backend health and owner data are responding.</span>
              </div>
            </div>

            <div className="launch-check-item">
              <span className="launch-check-icon">✓</span>
              <div>
                <strong>Products loaded</strong>
                <span>{products.length} sellable items in the demo catalog.</span>
              </div>
            </div>

            <div className="launch-check-item">
              <span className="launch-check-icon">✓</span>
              <div>
                <strong>Buyer leads active</strong>
                <span>{setupRequests.length} live setup request leads ready for follow-up.</span>
              </div>
            </div>

            <div className="launch-check-item">
              <span className="launch-check-icon">✓</span>
              <div>
                <strong>Close Kit ready</strong>
                <span>Pitch, proposal, follow-up, and full close kit copy tools are available.</span>
              </div>
            </div>

            <div className="launch-check-item">
              <span className="launch-check-icon">✓</span>
              <div>
                <strong>Orders visible</strong>
                <span>{orders.length} demo orders showing inside the owner console.</span>
              </div>
            </div>

            <div className="launch-check-item launch-check-item-final">
              <span className="launch-check-icon">✓</span>
              <div>
                <strong>Ready to pitch</strong>
                <span>Use this dashboard to show buyers a working storefront-to-owner workflow.</span>
              </div>
            </div>
          </div>
        </div>
        <div className="owner-panel wide close-kit-panel">
          <div className="panel-heading">
            <div>
              <p className="v3-kicker">Close Kit</p>
              <h2>Buyer Closing Tools</h2>
            </div>

            <span className="v3-pill online">READY</span>
          </div>

          <p className="muted close-kit-copy">
            Copy-ready sales tools for turning a live demo, setup request, or buyer conversation into a paid build.
          </p>

          <p id="close-kit-status" className="close-kit-status" hidden aria-live="polite"></p>

          <div className="close-kit-actions">
            <button
              type="button"
              className="close-kit-button"
              onClick={() =>
                copyCloseKitText(
                  "Buyer Pitch",
                  `I built a live storefront + owner dashboard demo that shows how your business can sell online, capture leads, track orders, and manage products from one simple command center.

The demo includes:
- Buyer-ready storefront
- Product/service offers
- Cart or request flow
- Owner dashboard
- Orders, inventory, and lead capture
- Launch-ready structure

This is built to help you move faster without starting from zero.`
                )
              }
            >
              Copy Buyer Pitch
            </button>

            <button
              type="button"
              className="close-kit-button"
              onClick={() =>
                copyCloseKitText(
                  "Proposal Summary",
                  `Proposal Summary

System: I AM THE ONE™ / WOLF OS™ SaaS
Package Options:
- Starter Storefront: $499+
- Pro Storefront + Owner Dashboard: $1,500+
- Custom SaaS Buildout: $3,000+

Core Build Includes:
- Live storefront
- Product/service offer cards
- Cart, checkout, or request flow
- Owner dashboard
- Order tracking
- Inventory controls
- Buyer lead capture
- Basic analytics/status panel
- Launch-ready brand structure

Next Step:
Confirm business details, offer list, pricing, timeline, payment method, and launch direction.`
                )
              }
            >
              Copy Proposal Summary
            </button>

            <button
              type="button"
              className="close-kit-button"
              onClick={() =>
                copyCloseKitText(
                  "Setup Follow-up",
                  `Hey ${setupRequests[0]?.name || "there"},

I reviewed the demo direction for ${setupRequests[0]?.business_name || "your business"}.

Based on what you sell — ${setupRequests[0]?.what_i_sell || "your products or services"} — I would recommend starting with a clean storefront and owner dashboard so you can present offers, capture buyer interest, and manage orders from one place.

The next step would be confirming:
1. Your main offers
2. Pricing
3. Timeline
4. Brand direction
5. Deposit/payment method
6. Launch plan

Once that is confirmed, the build can move from demo into production setup.

- Andrew Wolverton`
                )
              }
            >
              Copy Setup Follow-up
            </button>

            <button
              type="button"
              className="close-kit-button primary"
              onClick={() =>
                copyCloseKitText(
                  "Full Close Kit",
                  `FULL CLOSE KIT

Buyer Pitch:
I built a live storefront + owner dashboard demo that shows how your business can sell online, capture leads, track orders, and manage products from one simple command center.

System:
I AM THE ONE™ storefront + WOLF OS™ owner dashboard.

Offer:
Starter Storefront: $499+
Pro Storefront + Owner Dashboard: $1,500+
Custom SaaS Buildout: $3,000+

Includes:
- Live storefront
- Product/service cards
- Cart, checkout, or request flow
- Owner dashboard
- Order tracking
- Inventory controls
- Buyer lead capture
- Analytics/status panel
- Launch-ready structure

Current Demo Strength:
- ${setupRequests.length} live buyer leads loaded
- Commercial product catalog active
- Owner console online
- Demo orders visible
- Inventory value: ${money(inventoryValue)}

Close:
If the demo direction looks good, the next step is confirming content, pricing, timeline, deposit, and launch plan.`
                )
              }
            >
              Copy Full Close Kit
            </button>
          </div>
        </div>

        <div className="owner-panel wide">
          <div className="panel-heading">
            <div>
              <p className="v3-kicker">Setup Requests</p>
              <h2>Buyer Leads</h2>
            </div>

            <span className="v3-pill online">{setupRequests.length} LIVE</span>
          </div>

          {setupRequests.length ? (
            <div className="owner-table">
              {setupRequests.map((request) => (
                <div className="owner-row lead-row" key={request.id || `${request.email}-${request.created_at}`}>
                  <div className="lead-main">
                    <strong>{request.business_name || request.name || "Setup request"}</strong>
                    <span className="lead-contact">
                      {request.name || "Unknown buyer"} · {request.email || "No email"}
                    </span>
                    <span className="lead-detail">
                      {request.what_i_sell || "No business details yet"}
                    </span>
                  </div>

                                    <div className="lead-meta">
                    <span className="lead-badge">{displayLeadBudget(request)}</span>
                    <span
                      className={`lead-badge ${
                        isHotLead(request) ? "lead-hot" : "lead-follow"
                      }`}
                    >
                      {isHotLead(request) ? "HOT LEAD" : "FOLLOW UP"}
                    </span>
                    <span>{request.timeline || "Timeline TBD"}</span>
                    <span>{request.phone || request.website || "No phone/site"}</span>
                  </div>

                  <div className="lead-actions">
                    <a
                      className="owner-mini-link"
                      href={`mailto:${request.email || ""}?subject=${encodeURIComponent(
                        "Your I AM THE ONE™ setup request"
                      )}&body=${encodeURIComponent(
                        `Hi ${request.name || "there"},

Thanks for requesting setup help for ${
                          request.business_name || "your business"
                        }. I can help you get your storefront/demo set up.

- Andrew Wolverton`
                      )}`}
                    >
                      Email Buyer
                    </a>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">No setup requests yet.</p>
          )}
        </div>

        <div className="owner-panel wide">
          <div className="panel-heading">
            <div>
              <p className="v3-kicker">Real Orders</p>
              <h2>Orders</h2>
            </div>

            <span className="v3-pill online">LIVE</span>
          </div>

          {orders.length ? (
            <div className="owner-table">
              {orders.map((order) => (
                <div className="owner-table-row" key={order.id}>
                  <strong>{order.id}</strong>
                  <span>{order.buyer_name || "Unknown buyer"}</span>
                  <span>{money(order.total_cents)}</span>
                  <span>{order.payment_status || order.status || "pending"}</span>

                  {order.id && order.buyer_email ? (
                    <a
                      className="owner-mini-link"
                      href={apiUrl(
                        `/api/orders/${order.id}/download?email=${encodeURIComponent(
                          order.buyer_email
                        )}`
                      )}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Delivery
                    </a>
                  ) : (
                    <span>No email</span>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="ghost-card">No orders yet. Create one from /store/demo.</div>
          )}
        </div>

        <div className="owner-panel">
          <div className="panel-heading">
            <div>
              <p className="v3-kicker">Create Product</p>
              <h2>Add Item</h2>
            </div>
          </div>

          <form className="buyer-box" onSubmit={submitProduct}>
            <input
              value={form.store_slug}
              onChange={(event) => setField("store_slug", event.target.value)}
              placeholder="Store slug"
            />

            <input
              value={form.sku}
              onChange={(event) => setField("sku", event.target.value)}
              placeholder="SKU"
            />

            <input
              value={form.name}
              onChange={(event) => setField("name", event.target.value)}
              placeholder="Product name"
            />

            <input
              value={form.category}
              onChange={(event) => setField("category", event.target.value)}
              placeholder="Category"
            />

            <input
              value={form.description}
              onChange={(event) => setField("description", event.target.value)}
              placeholder="Description"
            />

            <input
              value={form.price_cents}
              onChange={(event) => setField("price_cents", event.target.value)}
              placeholder="Price cents, example 9900"
            />

            <input
              value={form.stock}
              onChange={(event) => setField("stock", event.target.value)}
              placeholder="Stock"
            />

            <input
              value={form.image_url}
              onChange={(event) => setField("image_url", event.target.value)}
              placeholder="Image URL"
            />

            <button className="v3-button primary full" type="submit">
              Create Product
            </button>
          </form>
        </div>
      </div>

      <div className="owner-panel">
        <div className="panel-heading">
          <div>
            <p className="v3-kicker">Real Inventory</p>
            <h2>Products</h2>
          </div>
        </div>

        {products.length ? (
          <div className="inventory-grid">
            {products.map((product, index) => (
              <div className="inventory-card" key={productKey(product, index)}>
                <strong>{product.name || product.sku}</strong>
                <span>{product.store_slug || product.store_name || "demo"}</span>
                <span>{product.sku || "NO-SKU"}</span>
                <span>{money(product.price_cents)}</span>
                <span>{Number(product.stock || 0)} stock</span>

                <div className="landing-actions">
                  <button
                    className="v3-button secondary"
                    onClick={() => onUpdateStock(product, Number(product.stock || 0) - 1)}
                  >
                    -1
                  </button>

                  <button
                    className="v3-button secondary"
                    onClick={() => onUpdateStock(product, Number(product.stock || 0) + 1)}
                  >
                    +1
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="ghost-card">No products returned yet.</div>
        )}
      </div>

      <div className="owner-panel">
        <div className="panel-heading">
          <div>
            <p className="v3-kicker">Stores</p>
            <h2>Tenants</h2>
          </div>
        </div>

        {stores.length ? (
          <div className="owner-table">
            {stores.map((store, index) => (
              <div className="owner-table-row" key={store.id || store.slug || index}>
                <strong>{store.name || store.slug}</strong>
                <span>{store.slug}</span>
                <span>{store.plan || "v3"}</span>
                <span>{store.status || "active"}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="ghost-card">No stores returned.</div>
        )}
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default App;







