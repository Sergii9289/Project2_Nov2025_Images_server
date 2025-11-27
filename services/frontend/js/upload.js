document.addEventListener('DOMContentLoaded', () => {
  const fileUpload = document.getElementById('file-upload');
  const imagesButton = document.getElementById('images-tab-btn');
  const dropzone = document.querySelector('.upload__dropzone');
  const currentUploadInput = document.querySelector('.upload__input');
  const copyButton = document.querySelector('.upload__copy');

  // Оновлення стилів вкладок
  const updateTabStyles = () => {
    const uploadTab = document.getElementById('upload-tab-btn');
    const imagesTab = document.getElementById('images-tab-btn');
    const isImagesPage = window.location.pathname.includes('images');

    uploadTab.classList.remove('upload__tab--active');
    imagesTab.classList.remove('upload__tab--active');

    if (isImagesPage) {
      imagesTab.classList.add('upload__tab--active');
    } else {
      uploadTab.classList.add('upload__tab--active');
    }
  };

  // Відправка файлу на сервер
  const uploadFileToServer = (file) => {
    const formData = new FormData();
    formData.append("file", file);

    return fetch("/upload/", {
      method: "POST",
      body: formData
    })
    .then(res => {
      if (!res.ok) throw new Error("Upload failed");
      return res.json();
    });
  };

  // Обробка файлів
  const handleAndStoreFiles = (files) => {
    if (!files || files.length === 0) return;

    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
    const MAX_SIZE_MB = 5;
    const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

    for (const file of files) {
      if (!allowedTypes.includes(file.type) || file.size > MAX_SIZE_BYTES) {
        alert(`Файл ${file.name} не підтримується або занадто великий.`);
        continue;
      }

      // Відправляємо на сервер
      uploadFileToServer(file)
        .then(data => {
          // data містить { filename: "1_<uuid>.jpg", url: "/images/1_<uuid>.jpg" }
          const storedFiles = JSON.parse(localStorage.getItem('uploadedImages')) || [];
          storedFiles.push({ name: data.filename, url: data.url });
          localStorage.setItem('uploadedImages', JSON.stringify(storedFiles));

          if (currentUploadInput) {
            currentUploadInput.value = data.url;
          }

          alert(`Файл ${data.filename} успішно завантажено!`);
          updateTabStyles();
        })
        .catch(err => {
          console.error("Upload error:", err);
          alert(`Не вдалося завантажити ${file.name}`);
        });
    }
  };

  // Кнопка копіювання
  if (copyButton && currentUploadInput) {
    copyButton.addEventListener('click', () => {
      const textToCopy = currentUploadInput.value;
      if (textToCopy && textToCopy !== 'https://') {
        navigator.clipboard.writeText(textToCopy).then(() => {
          copyButton.textContent = 'COPIED!';
          setTimeout(() => { copyButton.textContent = 'COPY'; }, 2000);
        }).catch(err => console.error('Failed to copy text: ', err));
      }
    });
  }

  // Перехід до галереї
  if (imagesButton) {
    imagesButton.addEventListener('click', () => {
      window.location.href = '/images/';
    });
  }

  // Вибір файлу через input
  if (fileUpload) {
    fileUpload.addEventListener('change', (event) => {
      handleAndStoreFiles(event.target.files);
      event.target.value = '';
    });
  }

  // Drag & Drop
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
    });
  });

  dropzone.addEventListener('drop', (event) => {
    handleAndStoreFiles(event.dataTransfer.files);
  });

  updateTabStyles();
});