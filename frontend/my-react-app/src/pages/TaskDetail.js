import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';
import Header1 from '../components/Header1';
import Footer from '../components/Footer';
import DisplayImage from './DisplayImage';
import './TaskDetail.css'; // スタイルシートを必要に応じて追加
import DisplayComment from './DisplayComment';

const TaskDetail = () => {
  const { taskId } = useParams();
  const [task, setTask] = useState(null);
  const [newComment, setNewComment] = useState('');

  // CSRFトークンを取得するAPIエンドポイントを呼び出す
  const fetchCsrfToken = async () => {
    try {
      const response = await axios.get('/api/csrf-token');
      return response.data.csrfToken;
    } catch (error) {
      console.error('Error fetching CSRF token:', error);
    }
  };

  useEffect(() => {
    const fetchTask = async () => {
      try {
        const response = await axios.get(`/api/tasks/${taskId}`);
        setTask(response.data);
      } catch (error) {
        console.error('Error fetching task details:', error);
      }
    };

    fetchTask();
  }, [taskId]);

  // リクエストにCSRFトークンを追加する
  const handleUpdate = async (event) => {
    event.preventDefault();
    const csrfToken = await fetchCsrfToken();
    const updatedTask = {
      content: event.target.content.value,
      description: event.target.description.value,
      due_date: event.target.due_date.value
    };
    try {
      await axios.post(`/api/tasks/${taskId}`, updatedTask, {
        headers: {
          'X-CSRFToken': csrfToken
        }
      });
      // 必要に応じてタスクを再取得して状態を更新
      fetchTask();
    } catch (error) {
      console.error('Error updating task:', error);
    }
  };

  const fetchTask = async () => {
    try {
      const response = await axios.get(`/api/tasks/${taskId}`);
      setTask(response.data);
    } catch (error) {
      console.error('Error fetching task details:', error);
    }
  };

  const handleAddComment = async (event) => {
    event.preventDefault();
    try {
      await axios.post(`/api/tasks/${taskId}/comments`, { content: newComment });
      setNewComment('');
      // コメントを追加した後、タスクデータを再取得
      fetchTask();
    } catch (error) {
      console.error('Error adding comment:', error);
    }
  };

  const handleDeleteComment = async (commentId) => {
    try {
      await axios.delete(`/api/comments/${commentId}`);
      fetchTask(); // 削除後にタスクデータを再取得
    } catch (error) {
      console.error('Error deleting comment:', error);
    }
  };

  if (!task) return <p>Loading...</p>;

  return (
    <div>
      <Header1 />
      <div className="container mt-4">
        <h2>Task Details</h2>
        <div className="task-detail">
          {/* タスクの更新フォーム */}
          <form onSubmit={handleUpdate} className="wide-form mb-4">
            <div className="mb-3">
              <label htmlFor="content" className="form-label">Content:</label>
              <input
                type="text"
                id="content"
                name="content"
                className="form-control"
                defaultValue={task.content}
              />
            </div>
            <div className="mb-3">
              <label htmlFor="description" className="form-label">Description:</label>
              <input
                type="text"
                id="description"
                name="description"
                className="form-control"
                defaultValue={task.description}
              />
            </div>
            <div className="mb-3">
              <label htmlFor="due_date" className="form-label">Due Date:</label>
              <input
                type="datetime-local"
                id="due_date"
                name="due_date"
                className="form-control"
                defaultValue={task.due_date}
              />
            </div>
            <button type="submit" className="btn btn-custom-update">Update Task</button>
          </form>

          {/* コメント追加フォーム */}
          <form onSubmit={handleAddComment} className="wide-form mt-4">
            <div className="mb-3">
              <label htmlFor="newComment" className="form-label">Add New Comment:</label>
              <input
                type="text"
                id="newComment"
                className="form-control"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
              />
            </div>
            <button type="submit" className="btn btn-custom">Add Comment</button>
          </form>

          {/* コメント表示 */}
          <div className="comments">
            <h3 className="mb-3">Comments</h3>
            {task.comments.length === 0 ? (
              <p>・No comments available</p>
            ) : (
              task.comments.map((comment) => (
                <DisplayComment
                  key={comment.id}
                  comment={comment}
                  onUpdate={fetchTask}
                  onDelete={() => handleDeleteComment(comment.id)}
                />
              ))
            )}
          </div>

          {/* 画像表示 */}
          <h3>Images</h3>
          {task.images && task.images.length === 0 ? (
            <p>・No images available</p> // 画像がない場合に表示するメッセージ
          ) : (
            <div className="image-container">
              {task.images && task.images.map((image) => (
                <DisplayImage
                  key={image.id}
                  imageId={image.id}
                  onDelete={fetchTask} 
                />
              ))}
            </div>
          )}

          {/* 戻るボタン */}
          <div className="btn-group mt-3">
            <button 
                onClick={() => window.history.back()}
                className="btn btn-secondary">
                Back
            </button>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default TaskDetail;
