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

  const displayFiles = () => {
    const storedFiles = JSON.parse(localStorage.getItem('uploadedImages')) || [];
    fileListWrapper.innerHTML = '';

    if (storedFiles.length === 0) {
      fileListWrapper.innerHTML = '<p class="upload__promt" style="text-align: center; margin-top: 50px;">Зображення ще не завантажено.</p>';
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
            <span class="file-icon"><img src="/static/image-uploader/img/icon/Group.png" alt="file icon"></span>
            <span class="file-name">${fileData.name}</span>
          </div>
          <div class="file-col file-col-url">
            <a href="/media/${fileData.name}" target="_blank">/media/${fileData.name}</a>
          </div>
          <div class="file-col file-col-delete">
            <button class="delete-btn" data-index="${index}">
              <img src="/static/image-uploader/img/icon/delete.png" alt="delete icon">
            </button>
          </div>
        `;
        list.appendChild(fileItem);
      });

      container.appendChild(list);
      fileListWrapper.appendChild(container);
      addDeleteListeners();
    }

    updateTabStyles();
  };

  const addDeleteListeners = () => {
    document.querySelectorAll('.delete-btn').forEach(button => {
      button.addEventListener('click', (event) => {
        const indexToDelete = parseInt(event.currentTarget.dataset.index);
        let storedFiles = JSON.parse(localStorage.getItem('uploadedImages')) || [];
        storedFiles.splice(indexToDelete, 1);
        localStorage.setItem('uploadedImages', JSON.stringify(storedFiles));
        displayFiles();
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