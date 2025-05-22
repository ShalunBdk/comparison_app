// static/main.js
document.addEventListener("DOMContentLoaded", function () {
  const dropZone1 = document.getElementById("drop-zone-1");
  const dropZone2 = document.getElementById("drop-zone-2");
  const fileInput1 = document.getElementById("file-input-1");
  const fileInput2 = document.getElementById("file-input-2");
  const compareBtn = document.getElementById("compare-button");
  const loadingDiv = document.getElementById("loading");
  const resultDiv = document.getElementById("result");

  let file1 = null;
  let file2 = null;

  // Обработчики событий для Drag & Drop
  setupDropZone(dropZone1, (file) => {
    file1 = file;
    dropZone1.textContent = "✅ Файл загружен: " + file.name;
    checkReady();
  });

  setupDropZone(dropZone2, (file) => {
    file2 = file;
    dropZone2.textContent = "✅ Файл загружен: " + file.name;
    checkReady();
  });

  // Обработчики событий для File Input
  fileInput1.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file && file.type.startsWith("image/")) {
      file1 = file;
      dropZone1.textContent = "✅ Файл загружен: " + file.name;
      checkReady();
    }
  });

  fileInput2.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file && file.type.startsWith("image/")) {
      file2 = file;
      dropZone2.textContent = "✅ Файл загружен: " + file.name;
      checkReady();
    }
  });

  // Проверка готовности кнопки
  function checkReady() {
    compareBtn.disabled = !(file1 && file2);
  }

  async function checkUsage() {
    try {
        const res = await fetch('/usage');
        const data = await res.json();
        if (data.limit_reached) {
        alert(`❌ Превышен лимит использования Vision API: ${data.count} из ${data.monthly_limit}`);
        document.getElementById('compare-button').disabled = true;
        return false;
        }
        return true;
    } catch (e) {
        console.error("Ошибка проверки лимита:", e);
        return true; // Разрешаем продолжить на случай ошибки
    }
    }

  // Логика сравнения
  compareBtn.addEventListener("click", async () => {
    if (!file1 || !file2) return;
    if(!checkUsage()) return;
    const formData = new FormData();
    formData.append("file1", file1);
    formData.append("file2", file2);

    loadingDiv.style.display = "block";
    resultDiv.style.display = "none";

    try {
      const res = await fetch("/compare/", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      let html = `
        <div class="similarity">🎯 Схожесть: ${data.similarity.toFixed(1)}%</div>
        <h3>📘 Эталонный текст:</h3>
        <div class="text-block">${data.text1}</div>
        <h3>📕 Текст для проверки:</h3>
        <div class="text-block">${data.text2}</div>
        <h3>📋 Найденные различия</h3>
      `;

      if (data.deleted.length > 0) {
        html += `<div>`;
        data.deleted.forEach(d => {
          html += `<div class="difference-item deleted">🗑️ Удалено: ${d.old}</div>`;
        });
        html += `</div>`;
      }

      if (data.modified.length > 0) {
        html += `<div>`;
        data.modified.forEach(m => {
          html += `<div class="difference-item modified">
                    🔄 Изменено (${m.similarity.toFixed(1)}%):<br>
                    Было: ${m.old}<br>
                    Стало: ${m.new}
                  </div>`;
        });
        html += `</div>`;
      }

      if (data.added.length > 0) {
        html += `<div>`;
        data.added.forEach(a => {
          html += `<div class="difference-item added">🟢 Добавлено: ${a.new}</div>`;
        });
        html += `</div>`;
      }

      if (data.deleted.length === 0 && data.modified.length === 0 && data.added.length === 0) {
        html += `<p>✅ Все строки совпадают с эталоном.</p>`;
      }

      resultDiv.innerHTML = html;
      resultDiv.style.display = "block";
    } catch (error) {
      resultDiv.innerHTML = `<p style="color:red;">❌ Ошибка: ${error.message}</p>`;
      resultDiv.style.display = "block";
    } finally {
      loadingDiv.style.display = "none";
    }
    updateUsageDisplay();
  });

  // Настройка зоны перетаскивания
  function setupDropZone(zone, onFileDrop) {
    zone.addEventListener("dragover", (e) => {
      e.preventDefault();
      zone.classList.add("dragover");
    });

    zone.addEventListener("dragleave", () => {
      zone.classList.remove("dragover");
    });

    zone.addEventListener("drop", (e) => {
      e.preventDefault();
      zone.classList.remove("dragover");

      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile && droppedFile.type.startsWith("image/")) {
        onFileDrop(droppedFile);
      } else {
        alert("Пожалуйста, перетащите изображение.");
      }
    });
  }

  async function updateUsageDisplay() {
    const res = await fetch('/usage');
    const data = await res.json();
    document.getElementById('usage-count').textContent = data.count;
    }

    window.addEventListener('load', updateUsageDisplay);
});