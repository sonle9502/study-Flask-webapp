import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import CreateTask from './pages/CreateTask';
import HomePage from './pages/HomePage';
import TaskDetail from './pages/TaskDetail';  

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/search" element={<HomePage />} />
          <Route path="/create-task" element={<CreateTask />} />
          <Route path="/tasks/:taskId" element={<TaskDetail />} /> 
          {/* 他のルートをここに追加 */}
        </Routes>
      </div>
    </Router>
  );
}

export default App;
