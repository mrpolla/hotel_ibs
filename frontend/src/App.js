import React, { useState, useEffect, useRef } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import "./App.css";

function App() {
  // State to store the search query, images returned for that query, and loading message.
  const [query, setQuery] = useState("pool");
  const [minPrice, setMinPrice] = useState("80");
  const [maxPrice, setMaxPrice] = useState("200");
  const [startDate, setStartDate] = useState(new Date("2025-04-05"));
  const [endDate, setEndDate] = useState(new Date("2025-04-08"));
  const [filteredImages, setFilteredImages] = useState([]);
  const [selectedImages, setSelectedImages] = useState([]);
  const [loadingMessage, setLoadingMessage] = useState("");
  const [hotels, setHotels] = useState([]);
  const [selectedHotels, setSelectedHotels] = useState([]);

  // Use useRef for the image cache to persist it across renders
  const imageCacheRef = useRef(new Map());

  // Only load from localStorage once when the component mounts
  useEffect(() => {
    console.log(
      "INITIALIZATION: Loading image cache from localStorage (should only happen once)"
    );
    try {
      const cachedImagesJSON = localStorage.getItem("imageCache");
      if (cachedImagesJSON) {
        const cachedImages = JSON.parse(cachedImagesJSON);
        // Convert array back to Map
        const cacheMap = new Map(cachedImages);
        imageCacheRef.current = cacheMap;
        console.log(
          `INITIALIZATION: Loaded ${cacheMap.size} cached images from localStorage`
        );
      }
    } catch (error) {
      console.error(
        "INITIALIZATION: Error loading image cache from localStorage:",
        error
      );
    }
  }, []);

  // Check if a pre-signed URL is expired.
  const isUrlExpired = (url) => {
    if (!url) return true;

    const match = url.match(/X-Amz-Expires=(\d+)&X-Amz-Date=(\d+)T(\d+)Z/);
    if (!match) return true;

    const expiresInSeconds = parseInt(match[1], 10);
    const dateStr = match[2];
    const timeStr = match[3];

    // Format: YYYYMMDDTHHMMSSZ
    const year = dateStr.slice(0, 4);
    const month = dateStr.slice(4, 6) - 1; // Months are 0-indexed in JS Date
    const day = dateStr.slice(6, 8);

    const hour = timeStr.slice(0, 2);
    const minute = timeStr.slice(2, 4);
    const second = timeStr.slice(4, 6);

    const signedDate = new Date(
      Date.UTC(year, month, day, hour, minute, second)
    );
    const expirationDate = new Date(
      signedDate.getTime() + expiresInSeconds * 1000
    );

    return Date.now() > expirationDate.getTime();
  };

  // Download an image and convert it into an object URL.
  const downloadImageUrl = async (url) => {
    try {
      console.log(
        `CACHING: Checking cache for URL: ${url.substring(0, 50)}...`
      );
      console.log(`CACHING: Cache size: ${imageCacheRef.current.size}`);

      // Check if the URL is in the cache
      console.log("CACHING: Checking cache for URL:", url);
      if (imageCacheRef.current.has(url)) {
        // Check if the URL has expired
        if (isUrlExpired(url)) {
          console.log(
            "CACHING: Cache HIT but URL EXPIRED. Downloading from S3..."
          );
        } else {
          console.log("CACHING: Cache HIT! Using cached image");
          return imageCacheRef.current.get(url);
        }
      } else {
        console.log(
          "CACHING: Cache MISS. URL not found in cache. Downloading from S3..."
        );
      }
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);

      // Update cache with new object URL
      console.log("CACHING: Adding new image to cache");
      imageCacheRef.current.set(url, objectUrl);

      // Save the updated cache to localStorage
      const cacheArray = Array.from(imageCacheRef.current.entries());
      localStorage.setItem("imageCache", JSON.stringify(cacheArray));
      console.log(
        `CACHING: Cache updated and saved. New size: ${imageCacheRef.current.size}`
      );

      return objectUrl;
    } catch (error) {
      console.error("CACHING: Error downloading image:", error);
      return null;
    }
  };

  // Fetch images from the backend based on the search query.
  const fetchImagesByTag = async (
    tag,
    minPrice,
    maxPrice,
    startDate,
    endDate
  ) => {
    const response = await fetch(
      `http://localhost:5000/api/images?tag=${encodeURIComponent(
        tag
      )}&minPrice=${encodeURIComponent(minPrice)}&maxPrice=${encodeURIComponent(
        maxPrice
      )}&startDate=${encodeURIComponent(
        startDate.toISOString()
      )}&endDate=${encodeURIComponent(endDate.toISOString())}`
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  };

  // Download images and attach object URLs for display.
  const downloadImages = async (images) => {
    const updatedImages = [];
    for (let index = 0; index < images.length; index++) {
      const image = images[index];
      const cacheKey = image.image_url;

      console.log(
        `DOWNLOADING: Processing image ${index + 1}/${images.length}`
      );
      let downloaded_url = await downloadImageUrl(cacheKey);

      updatedImages.push(downloaded_url ? { ...image, downloaded_url } : image);
      updateLoadingBar(10 + ((index + 1) / images.length) * 90); // Update loading bar based on progress
      setLoadingMessage(
        `Found ${images.length} results, downloading image ${
          index + 1
        } out of ${images.length}...`
      );
    }
    return updatedImages;
  };

  // Handle search operation: fetch images, download images, and update state.
  const handleSearch = async () => {
    if (query.trim() === "") return; // Do nothing if query is empty.
    console.log("SEARCH: Starting search for images with tag:", query);

    try {
      // Step 1: Fetch images based on the queried tag.
      setLoadingMessage("Searching database...");
      updateLoadingBar(10); // Update loading bar to 10%
      const imagesByTag = await fetchImagesByTag(
        query,
        minPrice,
        maxPrice,
        startDate,
        endDate
      );
      console.log(`SEARCH: Found ${imagesByTag.length} images for query`);

      if (!Array.isArray(imagesByTag)) {
        throw new Error("Invalid response format");
      }

      setLoadingMessage(
        `Found ${imagesByTag.length} results, downloading images...`
      );

      // Step 2: Download images to generate object URLs directly.
      const finalImages = await downloadImages(imagesByTag);

      // Step 3: Update state with the processed images.
      setLoadingMessage("Displaying images...");
      updateLoadingBar(100); // Update loading bar to 100%
      setFilteredImages(finalImages);
      setLoadingMessage("Done");

      // Clear the hotels and selectedHotels state
      setHotels([]);
      setSelectedHotels([]);
      setSelectedImages([]);
    } catch (error) {
      console.error("SEARCH: Error during search:", error);
      updateLoadingBar(0); // Reset loading bar on error
      setLoadingMessage("Error occurred: " + error.message);
    }
  };

  // Add a debug function to inspect the cache
  const debugCache = () => {
    console.log("DEBUG: Current image cache contents:");
    console.log(`DEBUG: Cache size: ${imageCacheRef.current.size}`);

    let i = 0;
    imageCacheRef.current.forEach((value, key) => {
      console.log(`DEBUG: [${i++}] Key: ${key.substring(0, 50)}...`);
      console.log(`DEBUG: [${i}] Value: ${value}`);
    });
  };

  // Make the debug function available globally
  useEffect(() => {
    window.debugImageCache = debugCache;
    console.log("DEBUG: debugImageCache function attached to window");
  }, []);

  // Handle the loading bar progress
  function updateLoadingBar(progress) {
    const loadingBarProgress = document.getElementById("loadingBarProgress");
    if (loadingBarProgress) {
      loadingBarProgress.style.width = progress + "%";
    }
  }

  // Handle double-click event to move images between containers
  const handleImageDoubleClick = (image, fromSelected) => {
    let updatedSelectedImages;
    if (fromSelected) {
      updatedSelectedImages = selectedImages.filter((img) => img !== image);
      setSelectedImages(updatedSelectedImages);
      setFilteredImages([...filteredImages, image]);
    } else {
      updatedSelectedImages = [...selectedImages, image];
      setSelectedImages(updatedSelectedImages);
      setFilteredImages(filteredImages.filter((img) => img !== image));
    }

    // Update selectedHotels based on selected images
    const updatedSelectedHotels = updatedSelectedImages
      .map((img) => ({
        hotel_id: img.hotel_id,
        name: img.hotel_name,
        avg_price_per_night: parseFloat(img.avg_price_per_night).toFixed(2),
      }))
      .filter(
        (hotel, index, self) =>
          index === self.findIndex((h) => h.hotel_id === hotel.hotel_id)
      );
    setSelectedHotels(updatedSelectedHotels);
  };

  return (
    <div className="container">
      <h1 className="title">Image Based Hotel Search</h1>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        placeholder="Enter image tag"
        className="input"
      />
      <input
        type="number"
        value={minPrice}
        onChange={(e) => setMinPrice(e.target.value)}
        placeholder="Min Price"
        className="input"
      />
      <input
        type="number"
        value={maxPrice}
        onChange={(e) => setMaxPrice(e.target.value)}
        placeholder="Max Price"
        className="input"
      />
      <DatePicker
        selected={startDate}
        onChange={(date) => setStartDate(date)}
        placeholderText="Start Date"
        className="input"
      />
      <DatePicker
        selected={endDate}
        onChange={(date) => setEndDate(date)}
        placeholderText="End Date"
        className="input"
      />
      <button onClick={handleSearch} className="button">
        Search
      </button>
      <div className="loading-bar">
        <div className="loading-bar-progress" id="loadingBarProgress"></div>
      </div>
      <div className="loading-message">{loadingMessage}</div>
      <div className="image-container-wrapper">
        <div className="image-container-sub-wrapper">
          <div className="image-container-label">Tagged images</div>
          <div className="image-container">
            {filteredImages.map((image, index) => (
              <img
                key={index}
                src={image.downloaded_url || image.image_url}
                alt={
                  image.tags
                    ? image.tags.map((tag) => tag.tag_name).join(", ")
                    : "Hotel image"
                }
                className="image"
                onDoubleClick={() => handleImageDoubleClick(image, false)}
              />
            ))}
          </div>
        </div>
        <div className="image-container-sub-wrapper">
          <div className="image-container-label">Selected images</div>
          <div className="image-container right">
            {selectedImages.map((image, index) => (
              <img
                key={index}
                src={image.downloaded_url || image.image_url}
                alt={
                  image.tags
                    ? image.tags.map((tag) => tag.tag_name).join(", ")
                    : "Selected hotel image"
                }
                className="image"
                onDoubleClick={() => handleImageDoubleClick(image, true)}
              />
            ))}
          </div>
        </div>
      </div>
      <div className="hotel-names-table">
        <table>
          <thead>
            <tr>
              <th style={{ width: "70%" }}>Hotel Name</th>
              <th style={{ width: "30%" }}>Average Price Per Night (€)</th>
            </tr>
          </thead>
          <tbody>
            {selectedHotels.map((hotel, index) => (
              <tr key={index}>
                <td>{hotel.name}</td>
                <td>€{hotel.avg_price_per_night}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default App;
