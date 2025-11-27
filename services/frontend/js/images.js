document.addEventListener('DOMContentLoaded', () => {
  document.addEventListener('keydown', function (event) {
    if (event.key === 'F5' || event.key === 'Escape') {
      event.preventDefault();
      window.location.href = '/form/upload.html';
    }
  });

  const fileListWrapper = document.getElementById('file-list-wrapper');
  const uploadRedirectButton = document.getElementById('upload-tab-btn');

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

  const displayFiles = async () => {
    try {
      const response = await fetch('/api/files');
      const storedFiles = await response.json(); // список з бекенду [{filename, display_name}, ...]

      fileListWrapper.innerHTML = '';

      if (!storedFiles || storedFiles.length === 0) {
        fileListWrapper.innerHTML =
          '<p class="upload__promt" style="text-align: center; margin-top: 50px;">Зображення ще не завантажено.</p>';
      } else {
        const container = document.createElement('div');
        container.className = 'file-list-container';

        const header = document.createElement('div');
        header.className = 'file-list-header';
        header.innerHTML = `
          <div class="file-col file-col-name">Назва</div>
          <div class="file-col file-col-url">Посилання</div>
          <div class="file-col file-col-delete">Видалити</div>
        `;
        container.appendChild(header);

        const list = document.createElement('div');
        list.id = 'file-list';

        storedFiles.forEach((fileData, index) => {
          const fileItem = document.createElement('div');
          fileItem.className = 'file-list-item';
          fileItem.innerHTML = `
            <div class="file-col file-col-name">
              <span class="file-icon"><img src="/frontend/img/icon/Group.png" alt="file icon"></span>
              <span class="file-name">${fileData.display_name}</span>
            </div>
            <div class="file-col file-col-url">
              <a href="/media/${fileData.filename}" target="_blank">${fileData.display_name}</a>
            </div>
            <div class="file-col file-col-delete">
              <button class="delete-btn" data-index="${index}" data-filename="${fileData.filename}">
                <img src="/frontend/img/icon/delete.png" alt="delete icon">
              </button>
            </div>
          `;
          list.appendChild(fileItem);
        });

        container.appendChild(list);
        fileListWrapper.appendChild(container);
        addDeleteListeners(storedFiles);
      }

      updateTabStyles();
    } catch (err) {
      console.error('✖ Failed to fetch files:', err);
      fileListWrapper.innerHTML =
        '<p class="upload__promt" style="text-align: center; margin-top: 50px;">Помилка отримання списку файлів.</p>';
    }
  };

  const addDeleteListeners = (storedFiles) => {
    document.querySelectorAll('.delete-btn').forEach(button => {
      button.addEventListener('click', async (event) => {
        const filename = event.currentTarget.dataset.filename;

        // Запит на бекенд для видалення файлу
        try {
          await fetch(`/api/delete/${filename}`, { method: 'DELETE' });
          displayFiles(); // оновлюємо список після видалення
        } catch (err) {
          console.error('✖ Failed to delete file:', err);
        }
      });
    });
  };

  if (uploadRedirectButton) {
    uploadRedirectButton.addEventListener('click', () => {
      window.location.href = '/upload/';
    });
  }

  displayFiles();
});