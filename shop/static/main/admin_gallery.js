// JavaScript for Color-Grouped Product Gallery in Django Admin (Safe DOM & Active Colors Management)

document.addEventListener("DOMContentLoaded", function() {
    const inlineGroup = document.getElementById("gallery-group");
    if (!inlineGroup) return;

    // Hide the default table but KEEP it intact in the DOM
    const tabularTable = inlineGroup.querySelector(".tabular");
    if (tabularTable) {
        tabularTable.style.position = "absolute";
        tabularTable.style.opacity = "0";
        tabularTable.style.height = "1px";
        tabularTable.style.width = "1px";
        tabularTable.style.overflow = "hidden";
        tabularTable.style.pointerEvents = "none";
    }

    // Create the container for our custom color-grouped gallery
    let customContainer = document.getElementById("custom-color-gallery");
    if (!customContainer) {
        customContainer = document.createElement("div");
        customContainer.id = "custom-color-gallery";
        customContainer.className = "color-gallery-container";
        inlineGroup.insertBefore(customContainer, inlineGroup.firstChild);
    }

    // Color names to Hex codes helper map for beautiful circles
    const colorHexMap = {
        "чорний": "#000000",
        "білий": "#ffffff",
        "червоний": "#e53935",
        "синій": "#1e88e5",
        "зелений": "#43a047",
        "жовтий": "#fdd835",
        "рожевий": "#f06292",
        "бузковий": "#c8a2c8",
        "масло": "#fbf2b5",
        "ірис": "#9f2b68",
        "сірий": "#9e9e9e",
        "фіолетовий": "#8e24aa",
        "бордовий": "#800020",
        "бежевий": "#f5f5dc",
        "блакитний": "#80d8ff",
        "коричневий": "#6d4c41",
        "помаранчевий": "#fb8c00"
    };

    function getColorHex(name) {
        const lower = name.toLowerCase().trim();
        for (const [key, val] of Object.entries(colorHexMap)) {
            if (lower.includes(key)) return val;
        }
        let hash = 0;
        for (let i = 0; i < name.length; i++) {
            hash = name.charCodeAt(i) + ((hash << 5) - hash);
        }
        let color = '#';
        for (let i = 0; i < 3; i++) {
            let value = (hash >> (i * 8)) & 0xFF;
            color += ('00' + value.toString(16)).substr(-2);
        }
        return color;
    }

    // Clean up temporary object URLs on unload
    const objectUrls = [];
    function createPreviewUrl(file) {
        const url = URL.createObjectURL(file);
        objectUrls.push(url);
        return url;
    }
    window.addEventListener("unload", () => {
        objectUrls.forEach(url => URL.revokeObjectURL(url));
    });

    function renderGallery() {
        // Save scroll position
        const scrollPos = window.scrollY;

        // Clean custom container but preserve the toolbar if it exists
        let toolbar = document.getElementById("gallery-toolbar");
        if (!toolbar) {
            toolbar = document.createElement("div");
            toolbar.id = "gallery-toolbar";
            toolbar.style.display = "flex";
            toolbar.style.alignItems = "center";
            toolbar.style.gap = "12px";
            toolbar.style.background = "#f9f9f9";
            toolbar.style.padding = "10px 15px";
            toolbar.style.borderRadius = "6px";
            toolbar.style.border = "1px solid #e0e0e0";
            toolbar.style.marginBottom = "20px";
        }
        
        customContainer.innerHTML = "";
        customContainer.appendChild(toolbar);

        const colors = [];
        colors.push({ id: "", name: "Загальні фото (без прив'язки до кольору)" });

        // Get selected colors from ManyToMany "colors" chosen box (id_colors_to)
        const colorsToSelect = document.getElementById("id_colors_to");
        const selectedColorIds = new Set();
        if (colorsToSelect) {
            Array.from(colorsToSelect.options).forEach(opt => {
                if (opt.value) {
                    selectedColorIds.add(opt.value);
                    colors.push({ id: opt.value, name: opt.text });
                }
            });
        }

        // Also check if any existing image inline has an assigned color that isn't currently in selected list
        const formRows = document.querySelectorAll('#gallery-group tbody tr.form-row:not(.empty-form)');
        formRows.forEach(row => {
            const colorDropdown = row.querySelector('select[name$="-color"]');
            if (colorDropdown && colorDropdown.value && !selectedColorIds.has(colorDropdown.value)) {
                const opt = Array.from(colorDropdown.options).find(o => o.value === colorDropdown.value);
                if (opt) {
                    selectedColorIds.add(opt.value);
                    colors.push({ id: opt.value, name: opt.text });
                }
            }
        });

        // Update the toolbar dropdown list of unused colors
        // All options are available from either the database list or default inline color selects
        const colorDropdown = document.querySelector('select[name^="gallery-"][name$="-color"]');
        const allSystemColors = [];
        if (colorDropdown) {
            Array.from(colorDropdown.options).forEach(opt => {
                if (opt.value && !selectedColorIds.has(opt.value)) {
                    allSystemColors.push({ id: opt.value, name: opt.text });
                }
            });
        }

        // Sort system colors alphabetically
        allSystemColors.sort((a, b) => a.name.localeCompare(b.name));

        // Populate Toolbar HTML
        toolbar.innerHTML = `
            <span style="font-size: 13px; font-weight: 600; color: #444;">Додати колір до галереї:</span>
            <select id="gallery-add-color-select" style="padding: 5px 10px; border-radius: 4px; border: 1px solid #ccc; font-size: 13px; background: #fff;">
                <option value="">-- Оберіть колір --</option>
                ${allSystemColors.map(c => `<option value="${c.id}">${c.name}</option>`).join("")}
            </select>
            <button type="button" id="gallery-add-color-btn" class="button" style="padding: 4px 14px; font-size: 12px; font-weight: 600; background: #f8bbd0; color: #880e4f; border: 1px solid #f48fb1; border-radius: 4px; cursor: pointer;">+ Додати колір</button>
        `;

        // Add event listener to toolbar button
        document.getElementById("gallery-add-color-btn").addEventListener("click", function() {
            const select = document.getElementById("gallery-add-color-select");
            const colorId = select.value;
            if (!colorId) return;

            // Move option using Django's SelectBox utility
            const fromSelect = document.getElementById("id_colors_from");
            const toSelect = document.getElementById("id_colors_to");
            if (fromSelect && toSelect && window.SelectBox) {
                const option = Array.from(fromSelect.options).find(opt => opt.value === colorId);
                if (option) {
                    option.selected = true;
                    window.SelectBox.move("id_colors_from", "id_colors_to");
                }
            } else {
                // Fallback for standard multiselect or standard elements
                const mainSelect = document.getElementById("id_colors");
                if (mainSelect) {
                    const option = Array.from(mainSelect.options).find(opt => opt.value === colorId);
                    if (option) {
                        option.selected = true;
                        mainSelect.dispatchEvent(new Event('change'));
                    }
                }
            }
            renderGallery();
        });

        // Loop through each active color category and render cards
        colors.forEach(color => {
            const matchedRows = [];
            
            formRows.forEach((row, index) => {
                const colorDropdown = row.querySelector('select[name$="-color"]');
                if (colorDropdown && colorDropdown.value === color.id) {
                    matchedRows.push({ row, index });
                }
            });

            // Create Color Card
            const card = document.createElement("div");
            card.className = "color-card";
            card.setAttribute("data-color-id", color.id);

            // Card Header
            const header = document.createElement("div");
            header.className = "color-card-header";
            
            if (color.id) {
                const dot = document.createElement("span");
                dot.className = "color-dot";
                dot.style.backgroundColor = getColorHex(color.name);
                header.appendChild(dot);
            }
            
            const title = document.createElement("strong");
            title.textContent = color.name;
            header.appendChild(title);

            // Add "Remove color" button next to name if it's a specific color category
            if (color.id) {
                const removeColorBtn = document.createElement("button");
                removeColorBtn.type = "button";
                removeColorBtn.className = "remove-color-link";
                removeColorBtn.style.marginLeft = "auto";
                removeColorBtn.style.background = "none";
                removeColorBtn.style.border = "none";
                removeColorBtn.style.color = "#d32f2f";
                removeColorBtn.style.cursor = "pointer";
                removeColorBtn.style.fontSize = "11px";
                removeColorBtn.style.fontWeight = "600";
                removeColorBtn.textContent = "Прибрати колір";
                
                removeColorBtn.addEventListener("click", function(e) {
                    e.stopPropagation();
                    // Alert if they have images
                    if (matchedRows.length > 0) {
                        if (!confirm(`У цьому кольорі є завантажені фото (${matchedRows.length} шт.). Якщо ви приберете колір, ці фото залишаться в загальній галереї. Продовжити?`)) {
                            return;
                        }
                        // Change color of matched inline rows to empty (general)
                        matchedRows.forEach(item => {
                            const colorDropdown = item.row.querySelector('select[name$="-color"]');
                            if (colorDropdown) {
                                colorDropdown.value = "";
                            }
                        });
                    }

                    // Move option using Django's SelectBox utility
                    const toSelect = document.getElementById("id_colors_to");
                    const fromSelect = document.getElementById("id_colors_from");
                    if (toSelect && fromSelect && window.SelectBox) {
                        const option = Array.from(toSelect.options).find(opt => opt.value === color.id);
                        if (option) {
                            option.selected = true;
                            window.SelectBox.move("id_colors_to", "id_colors_from");
                        }
                    } else {
                        // Fallback for standard multiselect
                        const mainSelect = document.getElementById("id_colors");
                        if (mainSelect) {
                            const option = Array.from(mainSelect.options).find(opt => opt.value === color.id);
                            if (option) {
                                option.selected = false;
                                mainSelect.dispatchEvent(new Event('change'));
                            }
                        }
                    }
                    renderGallery();
                });
                header.appendChild(removeColorBtn);
            }
            
            card.appendChild(header);

            // Card Grid
            const grid = document.createElement("div");
            grid.className = "gallery-grid";

            matchedRows.forEach(item => {
                const row = item.row;

                // References to real inputs inside the hidden row
                const fileInput = row.querySelector('input[type="file"]');
                const orderInput = row.querySelector('input[name$="-order"]');
                const deleteCheckbox = row.querySelector('input[name$="-DELETE"]');
                const originalLink = row.querySelector('td.field-image a');
                const djangoRemoveLink = row.querySelector('.inline-deletelink');
                const idInput = row.querySelector('input[name$="-id"]');

                const isDeleted = deleteCheckbox && deleteCheckbox.checked;

                // Visual item block
                const gItem = document.createElement("div");
                gItem.className = "gallery-item";
                gItem.style.cursor = "pointer";
                if (isDeleted) {
                    gItem.style.opacity = "0.35";
                    gItem.style.filter = "grayscale(1)";
                }

                // Image Preview
                let imgSrc = "";
                if (originalLink) {
                    const img = originalLink.querySelector("img");
                    if (img) imgSrc = img.src;
                }

                // Fallback to local preview if file was newly selected
                if (fileInput && fileInput.files && fileInput.files[0]) {
                    imgSrc = createPreviewUrl(fileInput.files[0]);
                }

                if (imgSrc) {
                    const previewImg = document.createElement("img");
                    previewImg.className = "gallery-item-image";
                    previewImg.src = imgSrc;
                    previewImg.alt = "Preview";
                    gItem.appendChild(previewImg);
                } else {
                    const placeholder = document.createElement("div");
                    placeholder.className = "gallery-item-placeholder";
                    placeholder.textContent = "📷";
                    gItem.appendChild(placeholder);
                }

                // Click handler on item to trigger file picker
                gItem.addEventListener("click", function(e) {
                    if (e.target.closest(".gallery-item-delete-btn") || e.target.closest("input")) {
                        return;
                    }
                    if (fileInput) {
                        fileInput.click();
                    }
                });

                // Controls container
                const controls = document.createElement("div");
                controls.className = "gallery-item-controls";

                // Selected File Name or upload prompt
                const fileLabel = document.createElement("div");
                fileLabel.style.fontSize = "10px";
                fileLabel.style.color = "#666";
                fileLabel.style.textAlign = "center";
                fileLabel.style.wordBreak = "break-all";
                
                if (fileInput && fileInput.files && fileInput.files[0]) {
                    fileLabel.textContent = fileInput.files[0].name;
                } else if (originalLink) {
                    fileLabel.textContent = "Завантажено";
                } else {
                    fileLabel.textContent = "Натисніть для вибору";
                }
                controls.appendChild(fileLabel);

                // Order input synced with hidden orderInput
                const orderContainer = document.createElement("div");
                orderContainer.className = "gallery-item-order";
                orderContainer.innerHTML = "<span>Сорт:</span>";
                
                const customOrder = document.createElement("input");
                customOrder.type = "number";
                customOrder.value = orderInput ? orderInput.value : "0";
                customOrder.style.width = "45px";
                customOrder.addEventListener("input", function() {
                    if (orderInput) {
                        orderInput.value = customOrder.value;
                    }
                });
                orderContainer.appendChild(customOrder);
                controls.appendChild(orderContainer);

                gItem.appendChild(controls);

                // Delete Button
                const isNewRow = !idInput || !idInput.value;
                const delBtn = document.createElement("button");
                delBtn.type = "button";
                delBtn.className = "gallery-item-delete-btn";
                delBtn.innerHTML = isDeleted ? "↺" : "✕";
                delBtn.title = isDeleted ? "Відновити" : "Видалити";
                
                delBtn.addEventListener("click", function(e) {
                    e.stopPropagation();
                    if (deleteCheckbox) {
                        deleteCheckbox.checked = !deleteCheckbox.checked;
                        renderGallery();
                    } else if (djangoRemoveLink) {
                        djangoRemoveLink.click();
                    } else if (isNewRow) {
                        const fallbackLink = row.querySelector('a.inline-deletelink, .delete a');
                        if (fallbackLink) {
                            fallbackLink.click();
                        } else {
                            row.remove();
                            const totalFormsInput = document.getElementById('id_gallery-TOTAL_FORMS');
                            if (totalFormsInput) {
                                totalFormsInput.value = Math.max(0, parseInt(totalFormsInput.value) - 1);
                            }
                            renderGallery();
                        }
                    }
                });
                gItem.appendChild(delBtn);

                grid.appendChild(gItem);
            });

            card.appendChild(grid);

            // Add Image Button
            const addBtn = document.createElement("button");
            addBtn.type = "button";
            addBtn.className = "add-image-to-color-btn";
            addBtn.textContent = "+ Додати зображення";
            addBtn.addEventListener("click", function() {
                const djangoAddLink = document.querySelector("#gallery-group .add-row a");
                if (djangoAddLink) {
                    djangoAddLink.click();
                    
                    const allRows = document.querySelectorAll('#gallery-group tbody tr.form-row:not(.empty-form)');
                    const newRow = allRows[allRows.length - 1];
                    
                    if (newRow) {
                        const colorDropdown = newRow.querySelector('select[name$="-color"]');
                        if (colorDropdown) {
                            colorDropdown.value = color.id;
                        }
                        
                        const fileInput = newRow.querySelector('input[type="file"]');
                        if (fileInput) {
                            fileInput.addEventListener("change", renderGallery);
                            fileInput.click();
                        }
                    }
                }
            });
            card.appendChild(addBtn);

            customContainer.appendChild(card);
        });

        // Restore scroll position
        window.scrollTo(0, scrollPos);
    }

    // Attach change event listeners to all current file inputs
    function attachChangeListeners() {
        document.querySelectorAll('#gallery-group input[type="file"]').forEach(input => {
            input.removeEventListener("change", renderGallery);
            input.addEventListener("change", renderGallery);
        });
    }

    // Initial load
    renderGallery();
    attachChangeListeners();

    // Watch for new inline form rows added by Django admin scripts
    const tbody = inlineGroup.querySelector("tbody");
    if (tbody) {
        const observer = new MutationObserver(function() {
            renderGallery();
            attachChangeListeners();
        });
        observer.observe(tbody, { childList: true });
    }

    // Watch ManyToMany colors field ("id_colors_to") for selected options changes
    const colorsToSelect = document.getElementById("id_colors_to");
    if (colorsToSelect) {
        const colorsObserver = new MutationObserver(function() {
            renderGallery();
            attachChangeListeners();
        });
        colorsObserver.observe(colorsToSelect, { childList: true });
    }
});
