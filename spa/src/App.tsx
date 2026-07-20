import { Form } from './features/locnet/Form';
import { useScrollBarWidth } from './ScrollBarWidth';
import './App.css';
import { IntlProvider } from './features/form/Intl';
import { TiDocument } from 'react-icons/ti'; // https://www.s-ings.com/typicons/

export const App = () => {
  useScrollBarWidth();

  return (
    <IntlProvider>
      <Form />
      <div id="printing-message">
        <TiDocument size="10rem" />
      </div>
    </IntlProvider>
  );
};

export default App;
