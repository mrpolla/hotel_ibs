const express = require("express");
const cors = require("cors");
const { Pool } = require("pg");
const AWS = require("aws-sdk");
require("dotenv").config();

const app = express();
const port = 5000;

// Middleware
app.use(cors());
app.use(express.json());

// PostgreSQL connection
const pool = new Pool({
  user: process.env.DB_USER,
  host: process.env.DB_HOST,
  database: process.env.DB_NAME,
  password: process.env.DB_PASSWORD,
  port: 5432,
});

// AWS S3 configuration
const s3 = new AWS.S3({
  accessKeyId: process.env.AWS_S3_accessKeyId,
  secretAccessKey: process.env.AWS_S3_secretAccessKey,
  region: process.env.AWS_S3_region,
});

// API endpoint to get images joined with hotels filtered by a queried tag.
app.get("/api/images", async (req, res) => {
  try {
    const { tag } = req.query;

    // Return an empty array if no tag is provided.
    if (!tag) {
      return res.json([]);
    }

    // SQL query to fetch images that have tags matching the provided query (case-insensitive).
    const queryText = `
      SELECT
          images.image_id,
          images.image_url,
          hotels.hotel_name,
          hotels.latitude,
          hotels.longitude, 
          COALESCE(
              json_agg(
                  json_build_object('tag_name', image_tags.tag_name, 'confidence_score', image_tags.confidence_score)
              ) FILTER (WHERE image_tags.tag_name IS NOT NULL),
              '[]'
          ) AS tags 
      FROM 
          images 
      JOIN hotels ON images.hotel_id = hotels.hotel_id
      LEFT JOIN image_tags ON images.image_id = image_tags.image_id::TEXT
      WHERE image_tags.tag_name ILIKE $1
      GROUP BY 
          images.image_id,
          hotels.hotel_name,
          hotels.latitude,
          hotels.longitude;
    `;

    // Execute the query with the tag as parameter.
    const values = [`%${tag}%`];
    const result = await pool.query(queryText, values);
    const images = result.rows;

    // Generate pre-signed URLs for each image.
    const updatedImages = images.map((image) => {
      console.log("Original image_url:", image.image_url);
      const signedUrl = s3.getSignedUrl("getObject", {
        Bucket: process.env.AWS_S3_bucket,
        Key: image.image_url.replace(/^\.\//, ""), // Remove a leading "./" if present.
        Expires: 60 * 60, // URL expiration time in seconds (e.g., 1 hour)
      });
      return { ...image, image_url: signedUrl };
    });

    res.json(updatedImages);
  } catch (error) {
    console.error("Error fetching images:", error);
    res.status(500).json({ error: "Internal Server Error" });
  }
});

app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});
