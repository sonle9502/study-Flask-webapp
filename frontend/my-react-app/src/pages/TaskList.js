// src/components/TaskList.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import DisplayImage from './DisplayImage';
import UploadImages from './UploadImages';
import { useNavigate, useLocation } from 'react-router-dom';
import { API_BASE_URL } from '../config';
import './TaskList.css';

const TaskList = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [tasks, setTasks] = useState([]);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const queryParam = params.get('query') || '';
    setQuery(queryParam);
    if (queryParam) {
      fetchResults(queryParam);
    } else {
      fetchTasks();
    }
  }, [location.search]);

  const fetchTasks = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tasks`, {
        method: 'GET',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setTasks(data);
    } catch (error) {
      console.error('Error fetching tasks:', error);
    }
  };

  const fetchResults = async (searchQuery) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/search`, {
        params: { query: searchQuery }
      });
      setResults(response.data);
    } catch (error) {
      console.error('Error fetching search results:', error);
    }
  };

  const deleteTask = async (taskId) => {
    try {
      await axios.delete(`${API_BASE_URL}/api/tasks/${taskId}`);
      query ? fetchResults(query) : fetchTasks();
    } catch (error) {
      console.error('Error deleting task:', error);
    }
  };

  return (
    <div className="container">
      <div className="list-group">
        <h1 style={{ color: 'black' }}>Hello, My tasks!</h1>
        {(query ? results : tasks).length === 0 ? (
          <p>No tasks found.</p>
        ) : (
          (query ? results : tasks).map((task) => (
            <div className="list-group-item" key={task.id}>
              <p>Content: {task.content}</p>
              <p>Detail: {task.description}</p>
              <p>Created At: {task.created_at}</p>
              <p>Due Date: {task.due_date}</p>
              <div className="image-container">
                {task.images && task.images.map((image) => (
                  <DisplayImage key={image.id} imageId={image.id} 
                    onDelete={() => query ? fetchResults(query) : fetchTasks()} 
                  />
                ))}
              </div>
              <div className="btn-group" role="group" aria-label="Task actions">
                <button 
                  onClick={() => {
                    if (window.confirm("Are you sure you want to delete this task?")) {
                      deleteTask(task.id);
                    }
                  }}
                  className="btn btn-danger">
                  Delete Task
                </button>
                <button 
                  onClick={() => navigate(`/tasks/${task.id}`)}
                  className="btn btn-primary">
                  View Details
                </button>
              </div>
              <UploadImages taskId={task.id} 
                onUploadSuccess={() => query ? fetchResults(query) : fetchTasks()} />
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default TaskList;
