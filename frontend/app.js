// =========================================================
// GREENLINE NAGPUR - CLIENT ENGINE & LEAFLET CONTROLLER
// =========================================================

let map = null;
let nodesData = [];
let vehiclesData = [];
let driversData = [];
let allOrdersData = [];
let standardPolyline = null;
let greenPolyline = null;
let nodeMarkersLayer = null;
let currentAuthToken = sessionStorage.getItem("greenline_token") || null;
let currentUser = JSON.parse(sessionStorage.getItem("greenline_user") || "null");
let gpsSocket = null;
let driverMarker = null;

// Nagpur Center Coordinates
const NAGPUR_CENTER = [21.1466, 79.0888];
const DEFAULT_ZOOM = 13;

// Fallback Nagpur Nodes in case of network latency
const FALLBACK_NODES = [
  { id: "mihan", name: "MIHAN Cargo Hub (South Zone)", lat: 21.0664, lon: 79.0534, elevation: 310, zone: "South Zone" },
  { id: "sitabuldi", name: "Sitabuldi Central Interchange", lat: 21.1466, lon: 79.0888, elevation: 314, zone: "Central Hub" },
  { id: "vnit", name: "VNIT Campus (West Zone)", lat: 21.1227, lon: 79.0494, elevation: 320, zone: "West Zone" },
  { id: "wardhaman_nagar", name: "Wardhaman Nagar (East Freight Zone)", lat: 21.1578, lon: 79.1350, elevation: 310, zone: "East Freight Zone" },
  { id: "kamptee_road", name: "Kamptee Road Logistics (North Zone)", lat: 21.1925, lon: 79.1120, elevation: 312, zone: "North Zone" },
  { id: "seminary_hills", name: "Seminary Hills Elevation Ridge", lat: 21.1702, lon: 79.0661, elevation: 375, zone: "North-West Ridge" },
  { id: "chhatrapati_sq", name: "Chhatrapati Square Junction", lat: 21.1135, lon: 79.0740, elevation: 314, zone: "South-Central" },
  { id: "dharampeth", name: "Dharampeth Commercial Corridor", lat: 21.1440, lon: 79.0680, elevation: 325, zone: "West-Central" },
  { id: "sadar", name: "Sadar Residency Road", lat: 21.1620, lon: 79.0840, elevation: 320, zone: "North-Central" }
];

document.addEventListener("DOMContentLoaded", async () => {
  initLucide();
  initMap();
  setupEventListeners();
  await loadNodes();
  await loadVehicles();
  await loadDrivers();
  await fetchEnvironmentTelemetry();
  await fetchDashboardMetrics();

  if (currentUser && currentAuthToken && sessionStorage.getItem("greenline_active") === "true") {
    hideLoginModal();
    applyRoleView(currentUser);
  } else {
    showLoginModal();
  }

  // Precompute sample route for map preview
  setTimeout(() => {
    if (currentUser && currentUser.role !== "Customer") {
      calculateRoute();
    }
  }, 500);
});

function initLucide() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

// ---------------------------------------------------------
// 1. LEAFLET MAP INITIALIZATION & SIZE INVALIDATION
// ---------------------------------------------------------
function initMap() {
  const mapElement = document.getElementById("map");
  if (!mapElement) {
    console.error("Map element #map not found in DOM");
    return;
  }

  try {
    map = L.map("map", {
      zoomControl: true,
      attributionControl: true
    }).setView(NAGPUR_CENTER, DEFAULT_ZOOM);

    // Reliable OpenStreetMap tile layer
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    nodeMarkersLayer = L.layerGroup().addTo(map);

    // Invalidate size after short delays to ensure DOM is fully laid out
    setTimeout(() => { map.invalidateSize(true); }, 150);
    setTimeout(() => { map.invalidateSize(true); }, 500);
    setTimeout(() => { map.invalidateSize(true); }, 1200);

    window.addEventListener("resize", () => {
      if (map) map.invalidateSize(true);
    });

  } catch (err) {
    console.error("Error initializing Leaflet map:", err);
  }
}

// ---------------------------------------------------------
// 2. DATA LOADING & POPULATION
// ---------------------------------------------------------
async function loadNodes() {
  try {
    const res = await fetch("/api/nodes");
    if (res.ok) {
      nodesData = await res.json();
    } else {
      nodesData = FALLBACK_NODES;
    }
  } catch (err) {
    console.warn("Using fallback nodes:", err);
    nodesData = FALLBACK_NODES;
  }

  const pickupSelect = document.getElementById("pickupNode");
  const deliverySelect = document.getElementById("deliveryNode");
  const custPickup = document.getElementById("custPickupNode");
  const custDelivery = document.getElementById("custDeliveryNode");

  if (pickupSelect) pickupSelect.innerHTML = "";
  if (deliverySelect) deliverySelect.innerHTML = "";
  if (custPickup) custPickup.innerHTML = "";
  if (custDelivery) custDelivery.innerHTML = "";

  nodesData.forEach(node => {
    const text = `${node.name} (${node.elevation}m)`;
    if (pickupSelect) {
      const opt = document.createElement("option");
      opt.value = node.id;
      opt.textContent = text;
      pickupSelect.appendChild(opt);
    }
    if (deliverySelect) {
      const opt = document.createElement("option");
      opt.value = node.id;
      opt.textContent = text;
      deliverySelect.appendChild(opt);
    }
    if (custPickup) {
      const opt = document.createElement("option");
      opt.value = node.id;
      opt.textContent = text;
      custPickup.appendChild(opt);
    }
    if (custDelivery) {
      const opt = document.createElement("option");
      opt.value = node.id;
      opt.textContent = text;
      custDelivery.appendChild(opt);
    }
  });

  // Default selection: MIHAN -> Sitabuldi
  if (pickupSelect) pickupSelect.value = "mihan";
  if (deliverySelect) deliverySelect.value = "sitabuldi";
  if (custPickup) custPickup.value = "mihan";
  if (custDelivery) custDelivery.value = "sitabuldi";

  renderNodeMarkers();
}

async function loadDrivers() {
  try {
    const res = await fetch("/api/drivers");
    if (res.ok) {
      driversData = await res.json();
    }
  } catch (err) {
    console.warn("Drivers fetch warning:", err);
  }
}

function renderNodeMarkers() {
  if (!map || !nodeMarkersLayer) return;
  nodeMarkersLayer.clearLayers();

  nodesData.forEach(node => {
    const isElevated = node.id === "seminary_hills" || node.elevation > 330;
    const isBottleneck = ["sitabuldi", "cotton_market", "central_avenue"].includes(node.id);
    const markerColor = isElevated ? "#f59e0b" : (isBottleneck ? "#ef4444" : "#10b981");

    const marker = L.circleMarker([node.lat, node.lon], {
      radius: isElevated || isBottleneck ? 8 : 6,
      fillColor: markerColor,
      color: "#ffffff",
      weight: 1.5,
      opacity: 1,
      fillOpacity: 0.9
    });

    marker.bindPopup(`
      <div class="text-slate-900 p-1 font-sans">
        <div class="font-bold text-xs">${node.name}</div>
        <div class="text-[11px] text-slate-600">${node.zone || "Nagpur Corridor"} • Elevation: <b>${node.elevation}m</b></div>
        <div class="mt-2 flex gap-1">
          <button onclick="setPickupFromMap('${node.id}')" class="px-2 py-0.5 bg-emerald-600 text-white rounded text-[10px] cursor-pointer">Set Pickup</button>
          <button onclick="setDeliveryFromMap('${node.id}')" class="px-2 py-0.5 bg-cyan-600 text-white rounded text-[10px] cursor-pointer">Set Delivery</button>
        </div>
      </div>
    `);

    nodeMarkersLayer.addLayer(marker);
  });
}

window.setPickupFromMap = function(nodeId) {
  document.getElementById("pickupNode").value = nodeId;
  if (map) map.closePopup();
  calculateRoute();
};

window.setDeliveryFromMap = function(nodeId) {
  document.getElementById("deliveryNode").value = nodeId;
  if (map) map.closePopup();
  calculateRoute();
};

async function loadVehicles() {
  try {
    const res = await fetch("/api/vehicles");
    if (res.ok) {
      vehiclesData = await res.json();
    } else {
      vehiclesData = [
        { id: 1, vehicle_type: "Electric Vehicle", age: 0, max_capacity: 500, registration_no: "MH-31-EV-2026" },
        { id: 2, vehicle_type: "Diesel", age: 6, max_capacity: 1200, registration_no: "MH-31-DV-4512" },
        { id: 3, vehicle_type: "Petrol", age: 3, max_capacity: 300, registration_no: "MH-31-PV-9876" }
      ];
    }
  } catch (err) {
    vehiclesData = [
      { id: 2, vehicle_type: "Diesel", age: 6, max_capacity: 1200, registration_no: "MH-31-DV-4512" }
    ];
  }

  const vehicleSelect = document.getElementById("vehicleProfile");
  vehicleSelect.innerHTML = "";

  vehiclesData.forEach(veh => {
    const opt = document.createElement("option");
    opt.value = veh.id;
    opt.textContent = `${veh.registration_no} [${veh.vehicle_type}] - Cap: ${veh.max_capacity}kg, Age: ${veh.age}y`;
    vehicleSelect.appendChild(opt);
  });

  const dieselIndex = vehiclesData.findIndex(v => v.vehicle_type.toLowerCase().includes("diesel"));
  if (dieselIndex >= 0) vehicleSelect.selectedIndex = dieselIndex;

  updateVehicleSpecsDisplay();
}

function updateVehicleSpecsDisplay() {
  const select = document.getElementById("vehicleProfile");
  const selectedId = parseInt(select.value);
  const veh = vehiclesData.find(v => v.id === selectedId);
  if (!veh) return;

  document.getElementById("vehicleSpecs").textContent = `${veh.vehicle_type} | Age: ${veh.age}y | Cap: ${veh.max_capacity}kg`;

  const slider = document.getElementById("cargoSlider");
  slider.max = veh.max_capacity;
  if (parseFloat(slider.value) > veh.max_capacity) {
    slider.value = Math.min(600, veh.max_capacity);
  }

  document.getElementById("maxCapacityLabel").textContent = `${veh.max_capacity} kg`;
  updateCargoRatioDisplay();
}

function updateCargoRatioDisplay() {
  const slider = document.getElementById("cargoSlider");
  const cargoKg = parseFloat(slider.value);
  document.getElementById("cargoDisplay").textContent = `${cargoKg} kg`;

  const select = document.getElementById("vehicleProfile");
  const veh = vehiclesData.find(v => v.id === parseInt(select.value));
  const maxCap = veh ? veh.max_capacity : 1200;
  const wm = (1 + (cargoKg / maxCap)).toFixed(2);
  document.getElementById("cargoRatioLabel").textContent = `W_m: ${wm}x`;
}

// ---------------------------------------------------------
// 3. AUTHENTICATION & ROLE-BASED ACCESS CONTROL
// ---------------------------------------------------------

function showLoginModal() {
  const modal = document.getElementById("loginModal");
  if (modal) modal.classList.remove("hidden");
}

function hideLoginModal() {
  const modal = document.getElementById("loginModal");
  if (modal) modal.classList.add("hidden");
}

async function loginAsQuick(username, role) {
  await loginWithCredentials(username, "greenline123", role);
}

async function handleFormLogin(event) {
  event.preventDefault();
  const username = document.getElementById("loginUsername").value.trim();
  const password = document.getElementById("loginPassword").value.trim();
  const role = document.getElementById("loginRole").value;
  await loginWithCredentials(username, password, role);
}

async function loginWithCredentials(username, password, role) {
  const errDiv = document.getElementById("loginErrorMsg");
  if (errDiv) errDiv.classList.add("hidden");

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: username, password: password })
    });

    if (!res.ok) {
      const err = await res.json();
      if (errDiv) {
        errDiv.textContent = err.detail || "Authentication failed. Check credentials.";
        errDiv.classList.remove("hidden");
      }
      return;
    }

    const data = await res.json();
    currentAuthToken = data.access_token;
    currentUser = data.user;
    
    // Save session
    sessionStorage.setItem("greenline_active", "true");
    sessionStorage.setItem("greenline_token", currentAuthToken);
    sessionStorage.setItem("greenline_user", JSON.stringify(currentUser));
    localStorage.removeItem("greenline_token");
    localStorage.removeItem("greenline_user");

    hideLoginModal();
    applyRoleView(currentUser);
    showToast(`Welcome, ${currentUser.name}!`, `Logged in as ${currentUser.role}`);

  } catch (err) {
    if (errDiv) {
      errDiv.textContent = "Unable to connect to server.";
      errDiv.classList.remove("hidden");
    }
  }
}

function logoutUser() {
  currentAuthToken = null;
  currentUser = null;
  sessionStorage.clear();
  localStorage.removeItem("greenline_token");
  localStorage.removeItem("greenline_user");
  
  // Reset UI
  document.getElementById("userName").textContent = "Not Logged In";
  document.getElementById("userRole").textContent = "Guest";
  document.getElementById("userAvatar").textContent = "--";

  // Hide portal and layouts
  const custPortal = document.getElementById("customerPortal");
  const adminLayout = document.getElementById("adminDriverLayout");
  const adminSec = document.getElementById("adminDispatchSection");
  const driverSec = document.getElementById("driverTripsSection");

  if (custPortal) custPortal.classList.add("hidden");
  if (adminLayout) adminLayout.classList.remove("hidden");
  if (adminSec) adminSec.classList.add("hidden");
  if (driverSec) driverSec.classList.add("hidden");

  showLoginModal();
  showToast("Logged Out", "Please sign in to access the platform.");
}

function updateUserUI(user) {
  if (!user) return;
  const nameEl = document.getElementById("userName");
  const roleEl = document.getElementById("userRole");
  const avatarEl = document.getElementById("userAvatar");

  if (nameEl) nameEl.textContent = user.name;
  if (roleEl) roleEl.textContent = user.role;
  if (avatarEl) {
    const initials = user.name.split(" ").map(n => n[0]).join("").toUpperCase();
    avatarEl.textContent = initials || "GL";
  }
}

function applyRoleView(user) {
  if (!user) {
    showLoginModal();
    return;
  }

  updateUserUI(user);

  const customerPortal = document.getElementById("customerPortal");
  const adminDriverLayout = document.getElementById("adminDriverLayout");
  const adminDispatchSection = document.getElementById("adminDispatchSection");
  const driverTripsSection = document.getElementById("driverTripsSection");
  const btnQuickTest = document.getElementById("btnQuickTest");
  const btnGpsToggle = document.getElementById("btnGpsToggle");
  const roleNavBadge = document.getElementById("roleNavBadge");

  if (user.role === "Customer") {
    // Customer Portal: NO MAP displayed!
    if (customerPortal) customerPortal.classList.remove("hidden");
    if (adminDriverLayout) adminDriverLayout.classList.add("hidden");
    if (btnQuickTest) btnQuickTest.classList.add("hidden");
    if (btnGpsToggle) btnGpsToggle.classList.add("hidden");
    if (roleNavBadge) {
      roleNavBadge.textContent = "Customer Portal";
      roleNavBadge.className = "text-[10px] sm:text-xs font-semibold px-2 py-0.5 rounded-full bg-sky-500/20 text-sky-400 border border-sky-500/30";
    }
    loadCustomerOrders();
  } else if (user.role === "Administrator") {
    // Admin View: Full Map Layout displayed!
    if (customerPortal) customerPortal.classList.add("hidden");
    if (adminDriverLayout) adminDriverLayout.classList.remove("hidden");
    if (adminDispatchSection) adminDispatchSection.classList.remove("hidden");
    if (driverTripsSection) driverTripsSection.classList.add("hidden");
    if (btnQuickTest) btnQuickTest.classList.remove("hidden");
    if (btnGpsToggle) btnGpsToggle.classList.remove("hidden");
    if (roleNavBadge) {
      roleNavBadge.textContent = "Administrator Console";
      roleNavBadge.className = "text-[10px] sm:text-xs font-semibold px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-400 border border-purple-500/30";
    }
    loadAdminOrders();
    if (map) {
      setTimeout(() => { map.invalidateSize(true); }, 200);
    }
  } else if (user.role === "Dispatch Driver") {
    // Driver View: Full Map Layout displayed!
    if (customerPortal) customerPortal.classList.add("hidden");
    if (adminDriverLayout) adminDriverLayout.classList.remove("hidden");
    if (adminDispatchSection) adminDispatchSection.classList.add("hidden");
    if (driverTripsSection) driverTripsSection.classList.remove("hidden");
    if (btnQuickTest) btnQuickTest.classList.remove("hidden");
    if (btnGpsToggle) btnGpsToggle.classList.remove("hidden");
    if (roleNavBadge) {
      roleNavBadge.textContent = "Driver Navigation";
      roleNavBadge.className = "text-[10px] sm:text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
    }
    loadDriverOrders();
    if (map) {
      setTimeout(() => { map.invalidateSize(true); }, 200);
    }
  }

  initLucide();
}

// ---------------------------------------------------------
// 3B. CUSTOMER ORDERS (BOOKING & ORDER HISTORY)
// ---------------------------------------------------------

async function handleCustomerOrderSubmit(e) {
  e.preventDefault();
  const pickup = document.getElementById("custPickupNode").value;
  const pickupAddr = document.getElementById("custPickupAddress").value.trim();
  const delivery = document.getElementById("custDeliveryNode").value;
  const deliveryAddr = document.getElementById("custDeliveryAddress").value.trim();
  const cargoWeight = parseFloat(document.getElementById("custCargoSlider").value) || 250;
  const notes = document.getElementById("custNotes").value.trim();

  if (pickup === delivery) {
    alert("Pickup and Dropoff locations must be different.");
    return;
  }

  const btn = document.getElementById("btnCustSubmitOrder");
  btn.disabled = true;
  btn.textContent = "Submitting Order...";

  try {
    const headers = { "Content-Type": "application/json" };
    if (currentAuthToken) headers["Authorization"] = `Bearer ${currentAuthToken}`;

    const res = await fetch("/api/orders", {
      method: "POST",
      headers: headers,
      body: JSON.stringify({
        pickup_node: pickup,
        pickup_address: pickupAddr,
        delivery_node: delivery,
        delivery_address: deliveryAddr,
        cargo_weight: cargoWeight,
        package_notes: notes
      })
    });

    if (!res.ok) {
      const err = await res.json();
      alert(`Order creation failed: ${err.detail || 'Server error'}`);
      return;
    }

    const order = await res.json();
    showToast("Booking Confirmed!", `Order #${order.id} submitted for Admin driver dispatch.`);
    document.getElementById("custNotes").value = "";
    loadCustomerOrders();
  } catch (err) {
    console.error("Order submission error:", err);
    alert("Network error while submitting order.");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="send" class="w-4 h-4 mr-2 inline"></i> SUBMIT ECO-DELIVERY REQUEST`;
    initLucide();
  }
}

async function loadCustomerOrders() {
  const container = document.getElementById("customerOrdersList");
  if (!container) return;

  try {
    const headers = {};
    if (currentAuthToken) headers["Authorization"] = `Bearer ${currentAuthToken}`;

    const res = await fetch("/api/orders?role=Customer", { headers });
    if (!res.ok) {
      container.innerHTML = `<div class="text-center py-8 text-slate-500 text-xs font-mono">No bookings found.</div>`;
      return;
    }

    const orders = await res.json();
    allOrdersData = orders;

    if (orders.length === 0) {
      container.innerHTML = `
        <div class="text-center py-12 text-slate-500 text-xs font-mono bg-slate-950/50 rounded-xl border border-slate-800 p-6">
          <i data-lucide="package" class="w-8 h-8 mx-auto mb-2 text-slate-600"></i>
          <div>No active delivery bookings yet.</div>
          <div class="text-[11px] text-slate-400 mt-1">Submit your first delivery request using the form on the left.</div>
        </div>
      `;
      initLucide();
      return;
    }

    container.innerHTML = orders.map(ord => {
      let statusBadge = "";
      if (ord.status === "PENDING") {
        statusBadge = `<span class="px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30 text-[10px] font-bold font-mono">⏳ Awaiting Admin Driver Assignment</span>`;
      } else if (ord.status === "ASSIGNED") {
        statusBadge = `<span class="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-bold font-mono">🚚 Driver Assigned: ${ord.driver ? ord.driver.name : 'Allocated'}</span>`;
      } else if (ord.status === "IN_TRANSIT") {
        statusBadge = `<span class="px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 text-[10px] font-bold font-mono">⚡ In Transit</span>`;
      } else if (ord.status === "DELIVERED") {
        statusBadge = `<span class="px-2.5 py-0.5 rounded-full bg-teal-500/20 text-teal-300 border border-teal-500/30 text-[10px] font-bold font-mono">✅ Delivered</span>`;
      }

      return `
        <div class="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-2.5 hover:border-slate-700 transition">
          <div class="flex items-center justify-between">
            <div class="text-xs font-bold text-white flex items-center gap-2">
              <span class="text-emerald-400 font-mono">#${ord.id}</span>
              <span>${ord.pickup_name} &rarr; ${ord.delivery_name}</span>
            </div>
            ${statusBadge}
          </div>

          <div class="text-[11px] text-slate-400 grid grid-cols-2 gap-2 border-t border-slate-800/80 pt-2">
            <div>
              <span class="text-slate-500">Pickup:</span> <span class="text-slate-300">${ord.pickup_address}</span>
            </div>
            <div>
              <span class="text-slate-500">Dropoff:</span> <span class="text-slate-300">${ord.delivery_address}</span>
            </div>
          </div>

          <div class="flex flex-wrap items-center justify-between text-[11px] text-slate-400 font-mono bg-slate-900/60 p-2 rounded-lg gap-2">
            <div>Cargo: <b class="text-slate-200">${ord.cargo_weight} kg</b></div>
            ${ord.co2_saved_percent !== null ? `<div>Eco-Savings: <b class="text-emerald-400">${ord.co2_saved_percent}% ΔCO₂</b></div>` : ''}
            ${ord.vehicle ? `<div>Vehicle: <b class="text-cyan-400">${ord.vehicle.vehicle_type} (${ord.vehicle.registration_no})</b></div>` : ''}
            <div>Booked: ${ord.created_at}</div>
          </div>
          ${ord.package_notes ? `<div class="text-[10px] text-slate-400 italic">Notes: ${ord.package_notes}</div>` : ''}
        </div>
      `;
    }).join("");

    initLucide();
  } catch (err) {
    console.error("Load customer orders error:", err);
  }
}

// ---------------------------------------------------------
// 3C. ADMIN DISPATCH & DRIVER ASSIGNMENT
// ---------------------------------------------------------

async function loadAdminOrders() {
  const container = document.getElementById("adminOrdersContainer");
  if (!container) return;

  try {
    const headers = {};
    if (currentAuthToken) headers["Authorization"] = `Bearer ${currentAuthToken}`;

    const res = await fetch("/api/orders?role=Administrator", { headers });
    if (!res.ok) return;

    const orders = await res.json();
    allOrdersData = orders;

    if (orders.length === 0) {
      container.innerHTML = `<div class="text-center py-6 text-slate-500 text-xs font-mono">No customer orders in queue.</div>`;
      return;
    }

    container.innerHTML = orders.map(ord => {
      const isPending = ord.status === "PENDING";
      
      const driverOptions = driversData.map(d => 
        `<option value="${d.id}" ${ord.driver && ord.driver.id === d.id ? 'selected' : ''}>${d.name}</option>`
      ).join("");

      const vehicleOptions = vehiclesData.map(v => 
        `<option value="${v.id}" ${ord.vehicle && ord.vehicle.id === v.id ? 'selected' : ''}>${v.registration_no} (${v.vehicle_type})</option>`
      ).join("");

      return `
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-3 space-y-2 text-xs">
          <div class="flex items-center justify-between">
            <div class="font-bold text-white flex items-center gap-1.5">
              <span class="text-purple-400 font-mono">#${ord.id}</span>
              <span>${ord.pickup_name} &rarr; ${ord.delivery_name}</span>
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold ${isPending ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'}">
              ${ord.status}
            </span>
          </div>

          <div class="text-[11px] text-slate-400 flex justify-between font-mono">
            <span>Customer: <b class="text-slate-200">${ord.customer ? ord.customer.name : 'Unknown'}</b></span>
            <span>Cargo: <b class="text-slate-200">${ord.cargo_weight} kg</b></span>
          </div>

          ${isPending ? `
            <div class="space-y-1.5 border-t border-slate-800 pt-2">
              <div class="text-[10px] text-purple-300 font-semibold uppercase">Assign Driver & Eco-Vehicle:</div>
              <div class="grid grid-cols-2 gap-1.5">
                <select id="assignDriverSelect_${ord.id}" class="bg-slate-950 border border-slate-700 text-[11px] rounded p-1.5 text-white focus:outline-none">
                  ${driverOptions || '<option value="3">Laxmikant Rakhade</option><option value="4">Vedant Sangrame</option>'}
                </select>
                <select id="assignVehicleSelect_${ord.id}" class="bg-slate-950 border border-slate-700 text-[11px] rounded p-1.5 text-white focus:outline-none">
                  ${vehicleOptions}
                </select>
              </div>
              <button onclick="assignDriver(${ord.id})" class="w-full py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs transition flex items-center justify-center gap-1 shadow">
                <i data-lucide="user-check" class="w-3.5 h-3.5"></i>
                <span>Assign Driver & Precompute Route</span>
              </button>
            </div>
          ` : `
            <div class="flex items-center justify-between text-[11px] font-mono border-t border-slate-800 pt-2">
              <span class="text-slate-400">Driver: <b class="text-emerald-400">${ord.driver ? ord.driver.name : '--'}</b></span>
              <button onclick="renderOrderRouteOnMap(${ord.id})" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-slate-700 rounded-lg text-[10px] flex items-center gap-1 transition">
                <i data-lucide="map-pin" class="w-3 h-3"></i>
                <span>View Route on Map</span>
              </button>
            </div>
          `}
        </div>
      `;
    }).join("");

    initLucide();
  } catch (err) {
    console.error("Load admin orders error:", err);
  }
}

async function assignDriver(orderId) {
  const driverSelect = document.getElementById(`assignDriverSelect_${orderId}`);
  const vehicleSelect = document.getElementById(`assignVehicleSelect_${orderId}`);
  if (!driverSelect) return;

  const driverId = parseInt(driverSelect.value);
  const vehicleId = vehicleSelect ? parseInt(vehicleSelect.value) : null;

  try {
    const headers = { "Content-Type": "application/json" };
    if (currentAuthToken) headers["Authorization"] = `Bearer ${currentAuthToken}`;

    const res = await fetch(`/api/orders/${orderId}/assign`, {
      method: "POST",
      headers: headers,
      body: JSON.stringify({ driver_id: driverId, vehicle_id: vehicleId })
    });

    if (!res.ok) {
      alert("Failed to assign driver.");
      return;
    }

    const updated = await res.json();
    showToast("Driver Assigned!", `Order #${orderId} assigned to ${updated.driver ? updated.driver.name : 'Driver'}.`);
    
    renderOrderRouteOnMap(orderId);
    loadAdminOrders();
    fetchDashboardMetrics();

  } catch (err) {
    console.error("Assign driver error:", err);
  }
}

// ---------------------------------------------------------
// 3D. DRIVER ASSIGNED DELIVERIES & NAVIGATION
// ---------------------------------------------------------

async function loadDriverOrders() {
  const container = document.getElementById("driverOrdersContainer");
  if (!container) return;

  try {
    const headers = {};
    if (currentAuthToken) headers["Authorization"] = `Bearer ${currentAuthToken}`;

    const res = await fetch("/api/orders?role=Dispatch Driver", { headers });
    if (!res.ok) return;

    const orders = await res.json();
    allOrdersData = orders;

    if (orders.length === 0) {
      container.innerHTML = `<div class="text-center py-6 text-slate-500 text-xs font-mono">No trips assigned to you yet.</div>`;
      return;
    }

    container.innerHTML = orders.map(ord => {
      const isAssigned = ord.status === "ASSIGNED";
      const isInTransit = ord.status === "IN_TRANSIT";
      const isDelivered = ord.status === "DELIVERED";

      return `
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-3 space-y-2.5 text-xs">
          <div class="flex items-center justify-between">
            <div class="font-bold text-white flex items-center gap-1.5">
              <span class="text-emerald-400 font-mono">#${ord.id}</span>
              <span>${ord.pickup_name} &rarr; ${ord.delivery_name}</span>
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold ${isDelivered ? 'bg-teal-500/20 text-teal-300 border border-teal-500/30' : (isInTransit ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30')}">
              ${ord.status}
            </span>
          </div>

          <div class="text-[11px] text-slate-400 grid grid-cols-2 gap-1 font-mono">
            <div>Cargo: <b class="text-slate-200">${ord.cargo_weight} kg</b></div>
            <div>CO₂ Saved: <b class="text-emerald-400">${ord.co2_saved_percent !== null ? ord.co2_saved_percent + '%' : '30%'}</b></div>
          </div>

          <div class="flex gap-2 border-t border-slate-800 pt-2">
            <button onclick="renderOrderRouteOnMap(${ord.id})" class="flex-1 py-1.5 px-2 bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-slate-700 rounded-lg text-xs font-medium transition flex items-center justify-center gap-1">
              <i data-lucide="navigation" class="w-3.5 h-3.5"></i>
              <span>Show Map Route</span>
            </button>

            ${isAssigned ? `
              <button onclick="updateOrderStatus(${ord.id}, 'IN_TRANSIT')" class="py-1.5 px-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-semibold transition">
                Start Trip
              </button>
            ` : ''}

            ${isInTransit ? `
              <button onclick="updateOrderStatus(${ord.id}, 'DELIVERED')" class="py-1.5 px-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold transition">
                Delivered
              </button>
            ` : ''}
          </div>
        </div>
      `;
    }).join("");

    initLucide();
  } catch (err) {
    console.error("Load driver orders error:", err);
  }
}

async function updateOrderStatus(orderId, newStatus) {
  try {
    const headers = { "Content-Type": "application/json" };
    if (currentAuthToken) headers["Authorization"] = `Bearer ${currentAuthToken}`;

    const res = await fetch(`/api/orders/${orderId}/status`, {
      method: "POST",
      headers: headers,
      body: JSON.stringify({ status: newStatus })
    });

    if (res.ok) {
      showToast("Status Updated", `Order #${orderId} marked as ${newStatus}.`);
      if (currentUser && currentUser.role === "Dispatch Driver") {
        loadDriverOrders();
      } else if (currentUser && currentUser.role === "Administrator") {
        loadAdminOrders();
      }
    }
  } catch (err) {
    console.error("Update status error:", err);
  }
}

function renderOrderRouteOnMap(orderId) {
  const ord = allOrdersData.find(o => o.id === orderId);
  if (!ord) return;

  if (ord.route_solution && ord.route_solution.green_route) {
    renderRouteResults(ord.route_solution, 15);
  } else {
    const pickupSelect = document.getElementById("pickupNode");
    const deliverySelect = document.getElementById("deliveryNode");
    if (pickupSelect) pickupSelect.value = ord.pickup_node;
    if (deliverySelect) deliverySelect.value = ord.delivery_node;
    calculateRoute();
  }
  showToast("Map Route Displayed", `${ord.pickup_name} to ${ord.delivery_name}`);
}

// ---------------------------------------------------------
// 4. ROUTE CALCULATION
// ---------------------------------------------------------
async function calculateRoute() {
  const pickup = document.getElementById("pickupNode").value;
  const delivery = document.getElementById("deliveryNode").value;

  if (pickup === delivery) {
    alert("Pickup hub and delivery destination must be distinct.");
    return;
  }

  const select = document.getElementById("vehicleProfile");
  const veh = vehiclesData.find(v => v.id === parseInt(select.value)) || {
    vehicle_type: "Diesel", age: 6.0, max_capacity: 1200.0, id: 2
  };

  const cargoLoad = parseFloat(document.getElementById("cargoSlider").value);
  const dispatchTime = document.getElementById("dispatchTime").value;

  const btnCalc = document.getElementById("btnCalculate");
  const timerSpan = document.getElementById("calcTimer");

  btnCalc.disabled = true;
  timerSpan.classList.remove("hidden");
  timerSpan.textContent = "Computing...";

  const startTime = performance.now();

  try {
    const payload = {
      pickup_node: pickup,
      delivery_node: delivery,
      cargo_load_kg: cargoLoad,
      max_capacity_kg: veh.max_capacity,
      vehicle_age: veh.age,
      vehicle_type: veh.vehicle_type,
      dispatch_time: dispatchTime,
      vehicle_id: veh.id
    };

    const headers = { "Content-Type": "application/json" };
    if (currentAuthToken) {
      headers["Authorization"] = `Bearer ${currentAuthToken}`;
    }

    const res = await fetch("/api/route/calculate", {
      method: "POST",
      headers: headers,
      body: JSON.stringify(payload)
    });

    const elapsedMs = Math.round(performance.now() - startTime);
    timerSpan.textContent = `${elapsedMs}ms`;

    if (!res.ok) {
      const err = await res.json();
      console.error("Calculation error detail:", err);
      return;
    }

    const data = await res.json();
    renderRouteResults(data, elapsedMs);
    await fetchDashboardMetrics();

  } catch (err) {
    console.error("Route calculation error:", err);
  } finally {
    btnCalc.disabled = false;
  }
}

// ---------------------------------------------------------
// 5. RESULTS RENDERING & ABSOLUTE MATH PROOF
// ---------------------------------------------------------
function renderRouteResults(solution, elapsedMs) {
  const std = solution.standard_route;
  const grn = solution.green_route;
  const comp = solution.comparison;
  const consts = solution.formula_constants;

  // Symmetrical Side-by-Side Cards
  document.getElementById("stdCarbon").textContent = `${std.total_carbon_g} g`;
  document.getElementById("stdDistance").textContent = `${std.total_distance_km} km`;
  document.getElementById("stdDuration").textContent = `${std.total_duration_min} min`;
  document.getElementById("stdIdle").textContent = `${std.total_idle_seconds} s`;

  document.getElementById("grnCarbon").textContent = `${grn.total_carbon_g} g`;
  document.getElementById("grnDistance").textContent = `${grn.total_distance_km} km`;
  document.getElementById("grnDuration").textContent = `${grn.total_duration_min} min`;
  document.getElementById("grnIdle").textContent = `${grn.total_idle_seconds} s`;

  // Savings Badges
  const deltaBadge = document.getElementById("badgeDeltaValue");
  deltaBadge.textContent = `${comp.delta_co2_percent}% ΔCO₂ Saved`;

  document.getElementById("co2SavedGrams").textContent = `${comp.co2_saved_grams} g`;
  document.getElementById("deltaDistance").textContent = `${comp.distance_difference_km > 0 ? "+" : ""}${comp.distance_difference_km} km`;
  document.getElementById("timeSavedMin").textContent = `${comp.time_saved_minutes} min`;

  // Proof-of-Formula Multipliers
  document.getElementById("proofEF").textContent = `${consts.EF_v} g/km (${consts.vehicle_type})`;
  document.getElementById("proofIF").textContent = `${consts.IF_v} g/sec`;
  document.getElementById("proofWm").textContent = `${consts.W_m} (Load: ${consts.active_cargo_kg}kg / ${consts.max_capacity_kg}kg)`;
  document.getElementById("proofAm").textContent = `${consts.A_m} (Age: ${consts.vehicle_age_years}y)`;

  // Segment Expansion Table
  const tbody = document.getElementById("proofSegmentsTbody");
  tbody.innerHTML = "";

  grn.segments.forEach(seg => {
    const math = seg.math_breakdown;
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-900/80 transition";

    const slopeBadge = seg.slope_percent > 5.0 
      ? `<span class="text-amber-400 font-bold">${seg.slope_percent}% (1.8x)</span>`
      : (seg.slope_percent < -2.0 
          ? `<span class="text-cyan-400">${seg.slope_percent}% (0.4x)</span>`
          : `<span class="text-slate-400">${seg.slope_percent}% (1.0x)</span>`);

    tr.innerHTML = `
      <td class="p-1.5 font-medium text-slate-300">
        <div>${seg.from_id} &rarr; ${seg.to_id}</div>
        <div class="text-[9px] text-slate-500">${seg.road_name}</div>
      </td>
      <td class="p-1.5 text-slate-300">${seg.distance_km} km</td>
      <td class="p-1.5">${slopeBadge}</td>
      <td class="p-1.5 font-mono text-emerald-400">${seg.idle_seconds}s (${seg.traffic_status})</td>
      <td class="p-1.5 font-bold text-emerald-300">${math.C_uv} g</td>
    `;
    tbody.appendChild(tr);
  });

  // Map Polylines Rendering
  renderPolylinesOnMap(std.coordinates, grn.coordinates);

  showToast("Eco-Route Computed", `Resolved in ${elapsedMs}ms • ${comp.delta_co2_percent}% Carbon Mitigated`);
}

function renderPolylinesOnMap(stdCoords, grnCoords) {
  if (!map) return;

  if (standardPolyline) map.removeLayer(standardPolyline);
  if (greenPolyline) map.removeLayer(greenPolyline);

  const stdLatLngs = stdCoords.map(c => [c.lat, c.lon]);
  const grnLatLngs = grnCoords.map(c => [c.lat, c.lon]);

  // Standard Baseline Route in Red (dashed line)
  standardPolyline = L.polyline(stdLatLngs, {
    color: "#f43f5e",
    weight: 4,
    opacity: 0.85,
    dashArray: "8, 6"
  }).addTo(map);

  standardPolyline.bindPopup("<b class='text-rose-600 font-sans'>Standard Shortest Route</b><br><span class='text-xs'>High congestion bottlenecks and steep gradients.</span>");

  // Eco-Optimal Green Route in Emerald Green (bold line)
  greenPolyline = L.polyline(grnLatLngs, {
    color: "#10b981",
    weight: 6,
    opacity: 0.95,
    lineCap: "round",
    lineJoin: "round"
  }).addTo(map);

  greenPolyline.bindPopup("<b class='text-emerald-600 font-sans'>Greenline Eco Route (A* Optimized)</b><br><span class='text-xs'>Topography & ML Traffic Carbon Minimized.</span>");

  // Smoothly fit bounds around both routes
  const combinedGroup = L.featureGroup([standardPolyline, greenPolyline]);
  map.fitBounds(combinedGroup.getBounds(), { padding: [50, 50] });

  setTimeout(() => { map.invalidateSize(true); }, 200);
}

// ---------------------------------------------------------
// 6. DASHBOARD & TELEMETRY
// ---------------------------------------------------------
async function fetchDashboardMetrics() {
  try {
    const res = await fetch("/api/dashboard/metrics");
    if (!res.ok) return;

    const data = await res.json();
    const summary = data.summary;

    document.getElementById("dbTotalTrips").textContent = `${summary.total_trips_optimized} Trips`;
    document.getElementById("dbCo2Saved").textContent = `${summary.total_co2_mitigated_kg} kg`;
    document.getElementById("dbAvgReduction").textContent = `${summary.average_co2_reduction_percent}%`;
    document.getElementById("dbTrees").textContent = `${summary.equivalent_trees_saved} 🌲`;
  } catch (err) {
    console.warn("Dashboard metrics note:", err);
  }
}

async function fetchEnvironmentTelemetry() {
  try {
    const weatherRes = await fetch("/api/weather");
    if (weatherRes.ok) {
      const wData = await weatherRes.json();
      const cur = wData.current || {};
      const temp = cur.temperature_2m !== undefined ? cur.temperature_2m : 31.4;
      const rh = cur.relative_humidity_2m !== undefined ? cur.relative_humidity_2m : 42;
      document.getElementById("weatherDisplay").textContent = `${temp}°C • ${rh}% RH`;
    }

    const aqiRes = await fetch("/api/aqi");
    if (aqiRes.ok) {
      const aData = await aqiRes.json();
      const curA = aData.current || {};
      const aqiVal = curA.european_aqi !== undefined ? curA.european_aqi : 52;
      document.getElementById("aqiDisplay").textContent = `AQI: ${aqiVal} (Moderate)`;
    }
  } catch (err) {
    console.warn("Telemetry note:", err);
  }
}

// ---------------------------------------------------------
// 7. EVENT LISTENERS & GEOLOCATION
// ---------------------------------------------------------
function setupEventListeners() {
  const btnCalc = document.getElementById("btnCalculate");
  if (btnCalc) btnCalc.addEventListener("click", calculateRoute);

  const btnQuick = document.getElementById("btnQuickTest");
  if (btnQuick) {
    btnQuick.addEventListener("click", () => {
      document.getElementById("pickupNode").value = "mihan";
      document.getElementById("deliveryNode").value = "sitabuldi";
      document.getElementById("cargoSlider").value = "600";
      document.getElementById("dispatchTime").value = "09:30";
      updateCargoRatioDisplay();
      calculateRoute();
    });
  }

  const slider = document.getElementById("cargoSlider");
  if (slider) slider.addEventListener("input", updateCargoRatioDisplay);

  const vehProfile = document.getElementById("vehicleProfile");
  if (vehProfile) vehProfile.addEventListener("change", updateVehicleSpecsDisplay);

  // Proof-of-Formula Accordion Toggle
  const btnToggleProof = document.getElementById("btnToggleProof");
  const proofContent = document.getElementById("proofContent");
  const proofChevron = document.getElementById("proofChevron");

  if (btnToggleProof && proofContent) {
    btnToggleProof.addEventListener("click", () => {
      const isHidden = proofContent.classList.contains("hidden");
      if (isHidden) {
        proofContent.classList.remove("hidden");
        if (proofChevron) proofChevron.style.transform = "rotate(180deg)";
      } else {
        proofContent.classList.add("hidden");
        if (proofChevron) proofChevron.style.transform = "rotate(0deg)";
      }
    });
  }

  // Geocoding Search
  const btnGeocode = document.getElementById("btnGeocodeSearch");
  if (btnGeocode) btnGeocode.addEventListener("click", performGeocodeSearch);

  const customAddress = document.getElementById("customAddressInput");
  if (customAddress) {
    customAddress.addEventListener("keypress", (e) => {
      if (e.key === "Enter") performGeocodeSearch();
    });
  }

  // GPS Live Tracking Toggle
  const btnGps = document.getElementById("btnGpsToggle");
  if (btnGps) btnGps.addEventListener("click", toggleLiveGps);
}

async function performGeocodeSearch() {
  const query = document.getElementById("customAddressInput").value.trim();
  if (!query) return;

  try {
    const res = await fetch(`/api/geocode?q=${encodeURIComponent(query + ", Nagpur")}`);
    if (!res.ok) {
      alert("Location not found in Nagpur. Please try a different landmark.");
      return;
    }
    const data = await res.json();
    const lat = data.lat;
    const lon = data.lon;

    if (map) {
      const searchMarker = L.marker([lat, lon]).addTo(map)
        .bindPopup(`<b>${data.name}</b><br><span class='text-xs'>Search Result</span>`).openPopup();
      map.setView([lat, lon], 15);
    }
    showToast("Location Found", `${data.name.substring(0, 45)}...`);
  } catch (err) {
    alert("Geocoding lookup failed.");
  }
}

function toggleLiveGps() {
  const statusSpan = document.getElementById("gpsStatusText");

  if (gpsSocket) {
    gpsSocket.close();
    gpsSocket = null;
    statusSpan.textContent = "Live GPS";
    showToast("GPS Stopped", "Live tracking disabled");
    return;
  }

  if (!navigator.geolocation) {
    alert("Geolocation is not supported by your browser.");
    return;
  }

  try {
    const wsProto = location.protocol === "https:" ? "wss:" : "ws:";
    gpsSocket = new WebSocket(`${wsProto}//${location.host}/ws/location`);

    gpsSocket.onopen = () => {
      statusSpan.textContent = "● Tracking";
      showToast("GPS Tracking", "Live driver broadcast active");
    };

    navigator.geolocation.watchPosition(
      pos => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;

        if (gpsSocket && gpsSocket.readyState === WebSocket.OPEN) {
          gpsSocket.send(JSON.stringify({ lat: lat, lon: lon }));
        }

        if (!driverMarker) {
          driverMarker = L.marker([lat, lon]).addTo(map).bindPopup("🚚 Live Delivery Vehicle");
        } else {
          driverMarker.setLatLng([lat, lon]);
        }
        if (map) map.setView([lat, lon], 14);
      },
      err => {
        statusSpan.textContent = "GPS Denied";
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  } catch (err) {
    console.error("GPS Socket error:", err);
  }
}

function showToast(title, desc) {
  const toast = document.getElementById("routeToast");
  document.getElementById("toastTitle").textContent = title;
  document.getElementById("toastDesc").textContent = desc;
  toast.classList.remove("hidden");
  setTimeout(() => {
    toast.classList.add("hidden");
  }, 4000);
}
