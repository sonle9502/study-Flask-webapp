import React, { useState, useEffect } from 'react';
import './Data.css'; // CSSファイルのインポート
import DisplayImage from './DisplayImage';
import UploadImages from './UploadImages';

function Data({ searchQuery }) {
  const [tasks, setTasks] = useState([]);

  // Function to fetch tasks based on the search query
  const fetchTasks = async (query = '') => {
    try {
      // Construct the URL based on the presence of a search query
      const url = query ? `/api/tasks?query=${encodeURIComponent(query)}` : '/api/tasks';
      const response = await fetch(url);
      const data = await response.json();
      setTasks(data);
    } catch (error) {
      console.error('Error fetching tasks:', error);
    }
  };

  // Fetch tasks when component mounts or searchQuery changes
  useEffect(() => {
    fetchTasks(searchQuery);
  }, [searchQuery]);

  return (
    <div>
      <h1>Tasks</h1>
      <div className="list-group">
        {tasks.map(task => (
          <div className="list-group-item" key={task.id}>
            <p>Content: {task.content}</p>
            <p>Detail: {task.description}</p>
            <p>Created At: {task.created_at}</p>
            <p>Due Date: {task.due_date}</p>
            {/* Display images associated with the task */}
            <div className="image-container">
              {task.images && task.images.map((image) => (
                <div key={image.id} className="image-item"> {/* Use image.id as key */}
                  <DisplayImage 
                    imageId={image.id} 
                    onDelete={async () => {
                      try {
                        // Wait for deletion to complete before refetching tasks
                        const response = await fetch(`/api/images/${image.id}`, { method: 'DELETE' });
                        if (response.ok) {
                          fetchTasks(searchQuery); // Refresh tasks list
                        } else {
                          console.error('Failed to delete image:', response.statusText);
                        }
                      } catch (error) {
                        console.error('Error deleting image:', error);
                      }
                    }}
                  />
                </div>
              ))}
            </div>
            <UploadImages 
              taskId={task.id} 
              onUploadSuccess={() => fetchTasks(searchQuery)} // Refresh tasks list on upload success
            />
          </div>
        ))}
      </div>
    </div>
  );
}

export default Data;
