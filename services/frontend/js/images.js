document.addEventListener('DOMContentLoaded', () => {
  // Перехід на /upload при F5 або Escape
  document.addEventListener('keydown', (event) => {
    if (event.key === 'F5' || event.key === 'Escape') {
      event.preventDefault();
      window.location.href = '/upload/';
    }
  });

  const fileListWrapper = document.getElementById('file-list-wrapper');
  const uploadRedirectButton = document.getElementById('upload-tab-btn');
  const ITEMS_PER_PAGE = 5;
  let currentPage = 1;

  // Активні стилі вкладок
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

  // Відображення файлів
  const displayFiles = async () => {
    try {
      const offset = (currentPage - 1) * ITEMS_PER_PAGE;
      const response = await fetch(`/api/files?limit=${ITEMS_PER_PAGE}&offset=${offset}`);
      const storedData = await response.json();

      const storedFiles = storedData.items || [];
      const totalCount = storedData.totalCount || 0;

      fileListWrapper.innerHTML = '';

      if (storedFiles.length === 0) {
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

        storedFiles.forEach((fileData) => {
          const fileItem = document.createElement('div');
          fileItem.className = 'file-list-item';

          const ext = fileData.filename.split('.').pop().toLowerCase();
          const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'webp'];
          const previewHtml = imageExts.includes(ext)
            ? `<img src="/media/${fileData.filename}" alt="${fileData.display_name}" style="max-width:40px; max-height:40px;">`
            : `<img src="/frontend/img/icon/Group.png" alt="file icon">`;

          fileItem.innerHTML = `
            <div class="file-col file-col-name">
              <span class="file-icon">${previewHtml}</span>
              <span class="file-name">${fileData.display_name}</span>
            </div>
            <div class="file-col file-col-url">
              <a href="/media/${fileData.filename}" target="_blank">${fileData.display_name}</a>
            </div>
            <div class="file-col file-col-delete">
              <button class="delete-btn" data-filename="${fileData.filename}">
                <img src="/frontend/img/icon/delete.png" alt="delete icon">
              </button>
            </div>
          `;
          list.appendChild(fileItem);
        });

        container.appendChild(list);
        fileListWrapper.appendChild(container);
        addDeleteListeners();

        // тепер викликаємо пагінацію
        renderPagination(totalCount);
      }

      updateTabStyles();
    } catch (err) {
      console.error('✖ Failed to fetch files:', err);
      fileListWrapper.innerHTML =
        '<p class="upload__promt" style="text-align: center; margin-top: 50px;">Помилка отримання списку файлів.</p>';
    }
  };

  // Пагінація
  const renderPagination = (totalItems) => {
    console.log('renderPagination called, totalItems:', totalItems);
    const paginationWrapper = document.getElementById('pagination-wrapper');
    paginationWrapper.innerHTML = '';

    const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);
    if (totalPages === 0) return;

    // Кнопка «Назад»
    const prevBtn = document.createElement('button');
    prevBtn.textContent = '«';
    prevBtn.disabled = currentPage === 1;
    prevBtn.addEventListener('click', () => {
      if (currentPage > 1) {
        currentPage--;
        displayFiles();
      }
    });
    paginationWrapper.appendChild(prevBtn);

    // Кнопки сторінок
    for (let i = 1; i <= totalPages; i++) {
      const btn = document.createElement('button');
      btn.className = 'pagination-btn';
      if (i === currentPage) btn.classList.add('active');
      btn.textContent = i;

      btn.addEventListener('click', () => {
        currentPage = i;
        displayFiles();
      });

      paginationWrapper.appendChild(btn);
    }

    // Кнопка «Вперед»
    const nextBtn = document.createElement('button');
    nextBtn.textContent = '»';
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.addEventListener('click', () => {
      if (currentPage < totalPages) {
        currentPage++;
        displayFiles();
      }
    });
    paginationWrapper.appendChild(nextBtn);
  };

  // Логіка видалення
  const addDeleteListeners = () => {
    document.querySelectorAll('.delete-btn').forEach((button) => {
      button.addEventListener('click', async (event) => {
        const filename = event.currentTarget.dataset.filename;
        try {
          await fetch(`/api/delete/${filename}`, { method: 'DELETE' });
          currentPage = Math.min(
            currentPage,
            Math.ceil((document.querySelectorAll('.file-list-item').length - 1) / ITEMS_PER_PAGE) || 1
          );
          displayFiles();
        } catch (err) {
          console.error('✖ Failed to delete file:', err);
        }
      });
    });
  };

  // Перехід на вкладку Upload
  if (uploadRedirectButton) {
    uploadRedirectButton.addEventListener('click', () => {
      window.location.href = '/upload/';
    });
  }

  displayFiles();
});