from datetime import datetime, timedelta

from airflow import DAG
from airflow.contrib.operators.kubernetes_pod_operator import \
    KubernetesPodOperator
from airflow.operators.dummy_operator import DummyOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime.utcnow(),
    'email': ['info@datafortress.cloud'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'tradingbot22-update-main', default_args=default_args, schedule_interval="0 23 */1 * *")

main_update = KubernetesPodOperator(namespace='default',
                        image="buildpack-deps:curl",
                        cmds=["curl" , "http://tradingbot-baseimage-service:8000/update"],
                        labels={"project": "tradingbot22"},
                        name="main-update",
                        task_id="main-update",
                        get_logs=True,
                        dag=dag
                        )

