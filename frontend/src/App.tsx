// Copyright © 2026 Andrew Wolverton. All Rights Reserved.

import React, { useEffect, useMemo, useState } from "react";

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

const API_BASE = cleanApiBase((import.meta as any).env?.VITE_BACKEND_URL);

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

function productKey(product: Product, index: number) {
  return String(product.id || product.sku || `product-${index}`);
}

function assetUrl(raw?: string | null) {
  const value = String(raw || "").trim();

  if (!value) return "";
  if (value.startsWith("http://") || value.startsWith("https://")) return value;
  if (value.startsWith("data:")) return value;

  if (value.startsWith("/")) {
    return `${API_BASE}${value}`;
  }

  return value;
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

function App() {
  const path = window.location.pathname;
  const storeSlug = getStoreSlug();

  const isOwner = path.startsWith("/owner");
  const isStore = path.startsWith("/store");

  const [health, setHealth] = useState<ApiHealth | null>(null);
  const [stores, setStores] = useState<Store[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
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

      const productsData = await apiJson<any>("/api/owner/products", {}, token).catch(() => ({
        products: []
      }));

      const storesData = await apiJson<any>("/api/owner/stores", {}, token).catch(() => ({
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
        <a href="/store/demo">Customer Store</a>
        <a href="/owner">Owner Console</a>
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
        <h1>Launch a premium storefront with checkout, orders, and owner control.</h1>
        <p>
          A live SaaS commerce demo built for creators, small brands, and service
          sellers who need a clean storefront, real checkout flow, inventory tracking,
          and an owner dashboard without starting from zero.
        </p>

        <div className="landing-actions">
          <a className="v3-button primary" href="/store/demo">
            View Live Store Demo
          </a>
          <a className="v3-button secondary" href="/owner">
            Open Owner Console
          </a>
        </div>

        <div className="shine-box">
          <strong>Demo owner access</strong>
          <span>Owner URL: /owner</span>
          <span>Password: WOLF-OWNER-2026</span>
          <span>Mode: Real API · Real orders · Manual payment</span>
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
        <p className="v3-kicker">Sellable Packages</p>
        <h2>Simple offer ladder</h2>

        <div className="metric-list">
          <Metric label="Demo Setup" value="$499+" />
          <Metric label="Pro Storefront" value="$1,500+" />
          <Metric label="SaaS Buildout" value="$5,000+" />
        </div>

        <div className="shine-box">
          <strong>What buyers get</strong>
          <span>Branded storefront</span>
          <span>Owner dashboard</span>
          <span>Product and order management</span>
          <span>Deploy-ready frontend and backend</span>
        </div>

        <div className="landing-actions">
          <a className="v3-button primary" href="/store/demo">
            Start Demo
          </a>
          <a className="v3-button secondary" href="mailto:awolf4277@gmail.com?subject=I%20AM%20THE%20ONE%20SaaS%20Setup">
            Request Setup
          </a>
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
          <small className="checkout-note">
            Last order: {lastOrder.id} · {money(lastOrder.total_cents)} ·{" "}
            {lastOrder.payment_status || "unpaid"}
          </small>
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

        <small>Owner passwords: WOLF-OWNER-2026 or WOLF-DEMO</small>
      </div>
    </section>
  );
}

function OwnerConsole({
  health,
  stores,
  orders,
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
    <section className="owner-console">
      <div className="owner-hero">
        <div>
          <p className="v3-kicker">Operator Mode</p>
          <h1>WOLF OS™ SaaS Command Center</h1>
          <p>
            Real owner dashboard connected to orders, products, stores, inventory,
            and backend health.
          </p>
        </div>

        <div className="owner-actions">
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
      </div>

      <div className="owner-panels">
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