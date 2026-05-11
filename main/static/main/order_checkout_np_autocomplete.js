document.addEventListener("DOMContentLoaded", () => {
    const cityInput = document.getElementById("id_city_input");
    const suggestionsBox = document.getElementById("city_suggestions");
    const deliveryTypeSelect = document.getElementById("id_delivery_type");
    const deliveryAddressInput = document.getElementById("id_address_input");
    const proxyUrl = window.NOVAPOSHTA_PROXY_URL;
    const cache = { cities: {}, warehouses: {} };

    if (!proxyUrl) console.error("❌ Proxy URL missing!");

    // --- Proxy для Нової Пошти ---
    function proxyNovaPoshta(method, data) {
        return fetch(proxyUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                modelName: "Address",
                calledMethod: method,
                methodProperties: data
            })
        }).then(r => r.json());
    }

    // --- Очистка підказок ---
    function clearSuggestions() {
        suggestionsBox.innerHTML = "";
        suggestionsBox.style.display = "none";
    }

    function highlightMatch(text, query) {
        const re = new RegExp(`(${query})`, "gi");
        return text.replace(re, "<strong>$1</strong>");
    }

    // --- Завантаження відділень NP ---
    function loadWarehouses(settlementRef) {
        if (!settlementRef) return;
        if (cache.warehouses[settlementRef]) {
            renderWarehouseSuggestions(cache.warehouses[settlementRef]);
            return;
        }

        proxyNovaPoshta("getWarehouses", { SettlementRef: settlementRef, Limit: 200 })
            .then(res => {
                if (!res.success || !res.data?.length) return;
                cache.warehouses[settlementRef] = res.data;
                renderWarehouseSuggestions(res.data);
            })
            .catch(err => console.error("Помилка завантаження відділень:", err));
    }

    function renderWarehouseSuggestions(warehouses) {
        const addressSuggestions = document.createElement("div");
        addressSuggestions.id = "address_suggestions";
        addressSuggestions.className = "np-suggestions";
        deliveryAddressInput.parentNode.appendChild(addressSuggestions);

        deliveryAddressInput.addEventListener("input", () => {
            const query = deliveryAddressInput.value.trim().toLowerCase();
            addressSuggestions.innerHTML = "";
            if (!query) return;

            const filtered = warehouses.filter(w =>
                w.Description.toLowerCase().includes(query) || w.Number.toLowerCase().includes(query)
            );

            filtered.forEach(w => {
                const item = document.createElement("div");
                item.className = "np-suggestion-item";
                item.innerHTML = highlightMatch(`${w.Description} (${w.Number})`, query);
                item.onclick = () => {
                    deliveryAddressInput.value = `${w.Description} (${w.Number})`;
                    addressSuggestions.innerHTML = "";
                };
                addressSuggestions.appendChild(item);
            });
        });

        document.addEventListener("click", e => {
            if (!addressSuggestions.contains(e.target) && e.target !== deliveryAddressInput) {
                addressSuggestions.innerHTML = "";
            }
        });
    }

    // --- Автопідказки міст NP ---
    let debounceTimer;
    cityInput.addEventListener("input", () => {
        const query = cityInput.value.trim();
        clearTimeout(debounceTimer);
        clearSuggestions();
        if (query.length < 2 || deliveryTypeSelect.value !== "NP") return;

        debounceTimer = setTimeout(() => {
            if (cache.cities[query]) {
                renderCitySuggestions(cache.cities[query], query);
                return;
            }

            proxyNovaPoshta("searchSettlements", { CityName: query, Limit: 8 })
                .then(res => {
                    if (!res.success || !res.data?.length) return;
                    const addresses = res.data[0].Addresses || [];
                    if (!addresses.length) return;
                    cache.cities[query] = addresses;
                    renderCitySuggestions(addresses, query);
                });
        }, 300);
    });

    function renderCitySuggestions(addresses, query) {
        suggestionsBox.style.display = "block";
        suggestionsBox.innerHTML = "";

        addresses.forEach(addr => {
            const displayName = [addr.MainDescription || addr.Present, addr.Area].filter(Boolean).join(", ");
            const settlementRef = addr.SettlementRef || addr.Ref;

            const item = document.createElement("div");
            item.className = "np-suggestion-item";
            item.innerHTML = highlightMatch(displayName, query);

            item.onclick = () => {
                cityInput.value = displayName;
                clearSuggestions();
                loadWarehouses(settlementRef);
            };
            suggestionsBox.appendChild(item);
        });
    }

    document.addEventListener("click", e => {
        if (!suggestionsBox.contains(e.target) && e.target !== cityInput) clearSuggestions();
    });

    // --- Зміна типу доставки ---
    deliveryTypeSelect.addEventListener("change", () => {
        clearSuggestions();
        cityInput.disabled = false;

        const type = deliveryTypeSelect.value;

        if (type === "NP") {
            deliveryAddressInput.placeholder = "Спочатку оберіть місто";
            deliveryAddressInput.readOnly = false;
            deliveryAddressInput.value = "";
        } else if (type === "UP") {
            deliveryAddressInput.placeholder = "Введіть адресу відділення Укрпошти";
            deliveryAddressInput.readOnly = false;
            deliveryAddressInput.value = "";
        } else if (type === "COURIER") {
            deliveryAddressInput.placeholder = "Введіть адресу доставки кур’єром";
            deliveryAddressInput.readOnly = false;
            deliveryAddressInput.value = "";
        } else if (type === "PICKUP") {
            const pickupAddress = "м. Кам'янець-Подільський, територія ринку, торговий дім 'Сяйво', магазин 'Світ білизни'";
            deliveryAddressInput.value = pickupAddress;
            deliveryAddressInput.readOnly = true;
        }
    });

    // --- Ініціалізація при завантаженні ---
    if (cityInput.value.trim() && deliveryTypeSelect.value === "NP") {
        proxyNovaPoshta("searchSettlements", { CityName: cityInput.value.trim(), Limit: 1 })
            .then(res => {
                if (res.success && res.data?.length && res.data[0].Addresses?.length) {
                    const addr = res.data[0].Addresses[0];
                    const settlementRef = addr.SettlementRef || addr.Ref;
                    cityInput.value = [addr.MainDescription || addr.Present, addr.Area].filter(Boolean).join(", ");
                    loadWarehouses(settlementRef);
                }
            });
    }
});











// document.addEventListener("DOMContentLoaded", () => {
//     const cityInput = document.getElementById("id_city_input");
//     const suggestionsBox = document.getElementById("city_suggestions");
//     const deliveryTypeSelect = document.getElementById("id_delivery_type");
//     const deliveryAddressGroup = document.getElementById("delivery_address_group");

//     const proxyUrl = window.NOVAPOSHTA_PROXY_URL;
//     const cache = { cities: {}, warehouses: {} };

//     if (!proxyUrl) {
//         console.error("❌ Proxy URL missing!");
//         return;
//     }

//     function proxyNovaPoshta(method, data) {
//         return fetch(proxyUrl, {
//             method: "POST",
//             headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({
//                 modelName: "Address",
//                 calledMethod: method,
//                 methodProperties: data
//             })
//         }).then(r => r.json());
//     }

//     function clearSuggestions() {
//         suggestionsBox.innerHTML = "";
//         suggestionsBox.style.display = "none";
//     }

//     function highlightMatch(text, query) {
//         const re = new RegExp(`(${query})`, "gi");
//         return text.replace(re, '<strong>$1</strong>');
//     }

//     // Завантаження відділень
//     function loadWarehouses(settlementRef) {
//         if (!settlementRef) return;

//         if (cache.warehouses[settlementRef]) {
//             renderWarehouseInput(cache.warehouses[settlementRef]);
//             return;
//         }

//         deliveryAddressGroup.innerHTML = `
//             <label for="id_address_input">Адреса доставки</label>
//             <input type="text" class="form-control" id="id_address_input" placeholder="Завантаження відділень..." disabled>
//             <div id="address_suggestions" class="np-suggestions"></div>
//         `;

//         proxyNovaPoshta("getWarehouses", { SettlementRef: settlementRef, Limit: 200 })
//             .then(res => {
//                 if (!res.success || !res.data?.length) {
//                     deliveryAddressGroup.innerHTML = `
//                         <label>Адреса доставки</label>
//                         <p class="text-danger">Відділення не знайдені.</p>
//                     `;
//                     return;
//                 }

//                 cache.warehouses[settlementRef] = res.data;
//                 renderWarehouseInput(res.data);
//             })
//             .catch(err => {
//                 console.error("❌ Помилка завантаження відділень:", err);
//                 deliveryAddressGroup.innerHTML = `
//                     <label>Адреса доставки</label>
//                     <p class="text-danger">Помилка завантаження відділень. Спробуйте пізніше.</p>
//                 `;
//             });
//     }

//     function renderWarehouseInput(warehouses) {
//         deliveryAddressGroup.innerHTML = `
//             <label for="id_address_input">Адреса доставки</label>
//             <input type="text" class="form-control" id="id_address_input" placeholder="Почніть вводити номер або назву відділення">
//             <div id="address_suggestions" class="np-suggestions"></div>
//         `;

//         const addressInput = document.getElementById("id_address_input");
//         const addressSuggestions = document.getElementById("address_suggestions");

//         addressInput.addEventListener("input", () => {
//             const query = addressInput.value.trim().toLowerCase();
//             addressSuggestions.innerHTML = "";
//             if (!query) return;

//             const filtered = warehouses.filter(w => w.Description.toLowerCase().includes(query) || w.Number.toLowerCase().includes(query));
//             if (!filtered.length) return;

//             filtered.forEach(w => {
//                 const item = document.createElement("div");
//                 item.className = "np-suggestion-item";
//                 item.innerHTML = highlightMatch(`${w.Description} (${w.Number})`, query);
//                 item.onclick = () => {
//                     addressInput.value = `${w.Description} (${w.Number})`;
//                     addressSuggestions.innerHTML = "";
//                 };
//                 addressSuggestions.appendChild(item);
//             });
//         });

//         document.addEventListener("click", e => {
//             if (!addressSuggestions.contains(e.target) && e.target !== addressInput) {
//                 addressSuggestions.innerHTML = "";
//             }
//         });
//     }

//     let debounceTimer;
//     cityInput.addEventListener("input", () => {
//         const query = cityInput.value.trim();
//         clearTimeout(debounceTimer);
//         clearSuggestions();

//         if (query.length < 2 || deliveryTypeSelect.value !== "NP") return;

//         debounceTimer = setTimeout(() => {
//             if (cache.cities[query]) {
//                 renderCitySuggestions(cache.cities[query], query);
//                 return;
//             }

//             proxyNovaPoshta("searchSettlements", { CityName: query, Limit: 8 })
//                 .then(res => {
//                     if (!res.success || !res.data?.length) {
//                         clearSuggestions();
//                         return;
//                     }

//                     const addresses = res.data[0].Addresses || [];
//                     if (!addresses.length) return;

//                     cache.cities[query] = addresses;
//                     renderCitySuggestions(addresses, query);
//                 });
//         }, 300);
//     });

//     function renderCitySuggestions(addresses, query) {
//         suggestionsBox.style.display = "block";
//         suggestionsBox.innerHTML = "";

//         addresses.forEach(addr => {
//             const displayName = [addr.MainDescription || addr.Present, addr.Area].filter(Boolean).join(", ");
//             const settlementRef = addr.SettlementRef || addr.Ref;

//             const item = document.createElement("div");
//             item.className = "np-suggestion-item";
//             item.innerHTML = highlightMatch(displayName, query);

//             item.onclick = () => {
//                 cityInput.value = displayName;
//                 clearSuggestions();
//                 if (settlementRef) loadWarehouses(settlementRef);
//             };

//             suggestionsBox.appendChild(item);
//         });
//     }

//     document.addEventListener("click", e => {
//         if (!suggestionsBox.contains(e.target) && e.target !== cityInput) {
//             clearSuggestions();
//         }
//     });

//     deliveryTypeSelect.addEventListener("change", () => {
//         clearSuggestions();
//         cityInput.disabled = false;
    
//         const type = deliveryTypeSelect.value;
    
//         if (type === "NP") {
//             // Нова Пошта — включаємо автопошук міст і відділень
//             deliveryAddressGroup.innerHTML = `
//                 <label for="id_address_input">Адреса доставки</label>
//                 <input type="text" class="form-control"
//                        name="delivery_address" id="id_address_input"
//                        placeholder="Спочатку оберіть місто">
//             `;
//             return;
//         }
    
//         if (type === "UP") {
//             // УкрПошта — ручне введення
//             deliveryAddressGroup.innerHTML = `
//                 <label for="id_address_input">Адреса доставки Укрпошти</label>
//                 <input type="text" class="form-control"
//                        name="delivery_address" id="id_address_input"
//                        placeholder="Введіть адресу відділення Укрпошти">
//             `;
//             return;
//         }
    
//         if (type === "COURIER") {
//             // Кур’єр
//             deliveryAddressGroup.innerHTML = `
//                 <label for="id_address_input">Адреса доставки кур’єром</label>
//                 <input type="text" class="form-control"
//                        name="delivery_address" id="id_address_input"
//                        placeholder="Введіть адресу доставки">
//             `;
//             return;
//         }
    
//         if (type === "PICKUP") {
//             // Самовивіз — автоматична адреса
//             deliveryAddressGroup.innerHTML = `
//                 <label for="id_address_input">Адреса пункту самовивозу</label>
//                 <textarea class="form-control" readonly
//                           name="delivery_address" id="id_address_input"
//                           rows="3">м. Кам'янець-Подільський, територія ринку,
//     торговий дім "Сяйво", магазин "Світ білизни"</textarea>
//             `;
//             return;
//         }
//     });
    

//     // Автовибір міста при завантаженні
//     if (cityInput.value.trim() && deliveryTypeSelect.value === "NP") {
//         proxyNovaPoshta("searchSettlements", { CityName: cityInput.value.trim(), Limit: 1 })
//             .then(res => {
//                 if (res.success && res.data?.length && res.data[0].Addresses?.length) {
//                     const addr = res.data[0].Addresses[0];
//                     const settlementRef = addr.SettlementRef || addr.Ref;
//                     const displayName = [addr.MainDescription || addr.Present, addr.Area].filter(Boolean).join(", ");
//                     cityInput.value = displayName;
//                     loadWarehouses(settlementRef);
//                 }
//             });
//     }
// });
