class Company(TableBase, table=True):
    __tablename__ = 'companies'
    
    user_id: int = Field(default=None, foreign_key="users.id")
    company_name: str = Field(default=None)
    industry: str = Field(default=None)
    phone: str = Field(default=None)
    email: str = Field(default=None)

class JobDescription(TableBase, table=True):
    __tablename__ = 'job_descriptions'

    user_id: int = Field(default=None, foreign_key="users.id")
    company_id: int = Field(default=None, foreign_key="companies.id")
    job_status: str = Field(default=None)
    job_title: str = Field(default=None)
    industries: List[str] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))
    is_favorite: bool = Field(default=True)

class Resume(TableBase, table=True):
    __tablename__ = 'resumes'    
    user_id: int = Field(default=None, foreign_key="users.id")
    job_id: int = Field(default=None, foreign_key="job_descriptions.id")

Please write SQLModel query to get "company_name", "industry" from "Company" table and "job_status", "job_title", "industries" from "JobDescription" table
but on the condition that is_favorite==True in JobDescription table