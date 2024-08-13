// src/pages/Search.js
import Header1 from '../components/Header1';
import Header2 from '../components/Header2';
import Footer from '../components/Footer';
import TaskList from './TaskList'
import ScrollToTopButton from '../components/ScrollToTopButton';

const Search = () => {
  return (
    <div>
      <Header1 />
      <Header2 />
      <TaskList />
      <Footer />
      <ScrollToTopButton />
    </div>
  );
};

export default Search;
