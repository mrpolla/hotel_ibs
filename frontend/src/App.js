import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [query, setQuery] = useState('');
  const [images, setImages] = useState([]);
  const [filteredImages, setFilteredImages] = useState([]);

  useEffect(() => {
    const cachedImages = localStorage.getItem('images');
    if (cachedImages) {
      const parsedImages = JSON.parse(cachedImages);
      setImages(parsedImages);
    } else {
      const fetchImages = async () => {
        try {
          const response = await fetch('http://localhost:5000/api/images');
          const data = await response.json();
          console.log('Fetched images:', data);
          setImages(data);
          localStorage.setItem('images', JSON.stringify(data));
        } catch (error) {
          console.error('Error fetching images:', error);
        }
      };

      fetchImages();
    }
  }, []);

  const handleSearch = async () => {
    console.log('Search query:', query);
    const filtered = images.filter(image => {
      console.log('Checking image:', image);
      return image.tags.some(tag => tag.tag_name.toLowerCase().includes(query.toLowerCase()));
    });
    console.log('Filtered images:', filtered);
    const downloadedImages = await Promise.all(
      filtered.map(async (image) => {
        const response = await fetch(image.image_url);
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        return { ...image, downloaded_url: url };
      })
    );
    setFilteredImages(downloadedImages);
  };

  return (
    <div className="container">
      <h1 className="title">Search Application</h1>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Enter image tag"
        className="input"
      />
      <button onClick={handleSearch} className="button">
        Search
      </button>
      <div className="image-container">
        {filteredImages.map((image, index) => (
          <img key={index} src={image.downloaded_url} alt={image.tags.map(tag => tag.tag_name).join(', ')} className="image" />
        ))}
      </div>
    </div>
  );
}

export default App;