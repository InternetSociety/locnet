import { useStaticFormTs } from '../form/useStaticFormTs';
import { StaticFormTsProvider } from '../form/FormProvider';
import { RenderNodes } from '../form/RenderNodes';
import { locNetFormResolver } from './formLogic';
import { locnetStaticFormValue, type EditableLocNetForm } from './formData';
import { editableLocNetModel, type EditableLocNetModel } from './model';
import { useLocNetServerSubmit } from './submit';
import styles from './Form.module.css';
import { DeveloperMenu } from './DeveloperMenu';
import { Header } from '../template/Header';

export const Form = () => {
  const useStaticFormResponse = useStaticFormTs<
    EditableLocNetForm,
    EditableLocNetModel
  >({
    resolver: locNetFormResolver,
    defaultForm: locnetStaticFormValue,
    defaultModel: editableLocNetModel,
  });

  const { useHandleSubmit, handleInvalid } = useStaticFormResponse;
  const handleLocNetServerSubmit = useLocNetServerSubmit();
  const submitHandler = useHandleSubmit(handleLocNetServerSubmit);

  return (
    <StaticFormTsProvider
      // @ts-expect-error TODO improve types
      value={useStaticFormResponse}
    >
      <Header />
      <main>
        <div className={styles.page}>
          <form onSubmit={submitHandler} onInvalid={handleInvalid}>
            <RenderNodes nodes={locnetStaticFormValue.nodes} id="nodes" />
          </form>

          <DeveloperMenu />
        </div>
      </main>
    </StaticFormTsProvider>
  );
};
