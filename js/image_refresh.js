function refreshImages(start = 1981, end = 2025) {
    const timestamp = new Date().getTime();
    const types = ['hurricane', 'tc', 'ace', 'pdi']
    // const imgIds = ['hurricane-img', 'tc-img', 'ace-img', 'pdi-img'];
  
    types.forEach(type1 => {
      const img = document.getElementById(`${type1}-img`);
      if (img) {
        const url = `/api/get_image?type=${type1.charAt(0).toUpperCase() + type1.slice(1)}&start_year=${start}&end_year=${end}&v=${timestamp}`;
        img.src = url;
      }
    });
  }
  
window.addEventListener("message", (event) => {
    if (event.data === "images_updated") {
      refreshImages();
    }
}, false);
  