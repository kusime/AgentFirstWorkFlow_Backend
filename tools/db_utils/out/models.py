from typing import Optional
import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, Double, ForeignKeyConstraint, Integer, PrimaryKeyConstraint, Table, Text, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class Accountflowgroup(Base):
    __tablename__ = 'accountflowgroup'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='accountflowgroup_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)

    account: Mapped[list['Account']] = relationship('Account', secondary='account_accountflowgroup', back_populates='accountflowgroup')


class Currencytype(Base):
    __tablename__ = 'currencytype'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='currencytype_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)

    account: Mapped[list['Account']] = relationship('Account', back_populates='currencytype')
    fxexchangecontrolrate: Mapped[list['Fxexchangecontrolrate']] = relationship('Fxexchangecontrolrate', foreign_keys='[Fxexchangecontrolrate.from_currency]', back_populates='currencytype')
    fxexchangecontrolrate_: Mapped[list['Fxexchangecontrolrate']] = relationship('Fxexchangecontrolrate', foreign_keys='[Fxexchangecontrolrate.to_currency]', back_populates='currencytype_')
    hole: Mapped[list['Hole']] = relationship('Hole', back_populates='currencytype')
    holetrace: Mapped[list['Holetrace']] = relationship('Holetrace', foreign_keys='[Holetrace.currency_type]', back_populates='currencytype')
    holetrace_: Mapped[list['Holetrace']] = relationship('Holetrace', foreign_keys='[Holetrace.from_currency]', back_populates='currencytype_')


class Flowtype(Base):
    __tablename__ = 'flowtype'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='flowtype_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)

    actiontype: Mapped[list['Actiontype']] = relationship('Actiontype', back_populates='flowtype')


class Holetype(Base):
    __tablename__ = 'holetype'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='holetype_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)

    hole: Mapped[list['Hole']] = relationship('Hole', back_populates='holetype')


class Theholelevel(Base):
    __tablename__ = 'theholelevel'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='theholelevel_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[str] = mapped_column(Text, nullable=False)

    hole: Mapped[list['Hole']] = relationship('Hole', back_populates='theholelevel')


class Tracetype(Base):
    __tablename__ = 'tracetype'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='tracetype_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)

    holetrace: Mapped[list['Holetrace']] = relationship('Holetrace', back_populates='tracetype')


class Account(Base):
    __tablename__ = 'account'
    __table_args__ = (
        ForeignKeyConstraint(['currency_type'], ['currencytype.id'], ondelete='CASCADE', name='account_currency_type_fkey'),
        ForeignKeyConstraint(['logic_account'], ['account.id'], ondelete='SET NULL', name='account_logic_account_fkey'),
        PrimaryKeyConstraint('id', name='account_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    currency_type: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    max_debt_capacity: Mapped[Optional[float]] = mapped_column(Double(53))
    soft_limit: Mapped[Optional[float]] = mapped_column(Double(53))
    logic_account: Mapped[Optional[int]] = mapped_column(Integer)

    currencytype: Mapped['Currencytype'] = relationship('Currencytype', back_populates='account')
    account: Mapped[Optional['Account']] = relationship('Account', remote_side=[id], back_populates='account_reverse')
    account_reverse: Mapped[list['Account']] = relationship('Account', remote_side=[logic_account], back_populates='account')
    accountflowgroup: Mapped[list['Accountflowgroup']] = relationship('Accountflowgroup', secondary='account_accountflowgroup', back_populates='account')
    hole: Mapped[list['Hole']] = relationship('Hole', back_populates='account_')
    holetrace: Mapped[list['Holetrace']] = relationship('Holetrace', back_populates='account')


class Actiontype(Base):
    __tablename__ = 'actiontype'
    __table_args__ = (
        ForeignKeyConstraint(['flow_type'], ['flowtype.id'], ondelete='CASCADE', name='actiontype_flow_type_fkey'),
        PrimaryKeyConstraint('id', name='actiontype_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    flow_type: Mapped[int] = mapped_column(Integer, nullable=False)

    flowtype: Mapped['Flowtype'] = relationship('Flowtype', back_populates='actiontype')
    holetrace: Mapped[list['Holetrace']] = relationship('Holetrace', back_populates='actiontype')


class Fxexchangecontrolrate(Base):
    __tablename__ = 'fxexchangecontrolrate'
    __table_args__ = (
        ForeignKeyConstraint(['from_currency'], ['currencytype.id'], ondelete='CASCADE', name='fxexchangecontrolrate_from_currency_fkey'),
        ForeignKeyConstraint(['to_currency'], ['currencytype.id'], ondelete='CASCADE', name='fxexchangecontrolrate_to_currency_fkey'),
        PrimaryKeyConstraint('id', name='fxexchangecontrolrate_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_currency: Mapped[int] = mapped_column(Integer, nullable=False)
    to_currency: Mapped[int] = mapped_column(Integer, nullable=False)
    currency_rate: Mapped[Optional[float]] = mapped_column(Double(53))

    currencytype: Mapped['Currencytype'] = relationship('Currencytype', foreign_keys=[from_currency], back_populates='fxexchangecontrolrate')
    currencytype_: Mapped['Currencytype'] = relationship('Currencytype', foreign_keys=[to_currency], back_populates='fxexchangecontrolrate_')


t_account_accountflowgroup = Table(
    'account_accountflowgroup', Base.metadata,
    Column('account', Integer, primary_key=True),
    Column('accountflowgroup', Integer, primary_key=True),
    ForeignKeyConstraint(['account'], ['account.id'], name='account_accountflowgroup_account_fkey'),
    ForeignKeyConstraint(['accountflowgroup'], ['accountflowgroup.id'], name='account_accountflowgroup_accountflowgroup_fkey'),
    PrimaryKeyConstraint('account', 'accountflowgroup', name='account_accountflowgroup_pkey')
)


class Hole(Base):
    __tablename__ = 'hole'
    __table_args__ = (
        ForeignKeyConstraint(['account'], ['account.id'], ondelete='CASCADE', name='hole_account_fkey'),
        ForeignKeyConstraint(['currency_type'], ['currencytype.id'], ondelete='CASCADE', name='hole_currency_type_fkey'),
        ForeignKeyConstraint(['hole_type'], ['holetype.id'], ondelete='CASCADE', name='hole_hole_type_fkey'),
        ForeignKeyConstraint(['the_hole_level'], ['theholelevel.id'], ondelete='CASCADE', name='hole_the_hole_level_fkey'),
        PrimaryKeyConstraint('id', name='hole_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    the_hole_level: Mapped[int] = mapped_column(Integer, nullable=False)
    currency_type: Mapped[int] = mapped_column(Integer, nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    account: Mapped[int] = mapped_column(Integer, nullable=False)
    hole_type: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[Optional[float]] = mapped_column(Double(53))
    is_currency_locked: Mapped[Optional[bool]] = mapped_column(Boolean)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    require_physical_account: Mapped[Optional[bool]] = mapped_column(Boolean)

    account_: Mapped['Account'] = relationship('Account', back_populates='hole')
    currencytype: Mapped['Currencytype'] = relationship('Currencytype', back_populates='hole')
    holetype: Mapped['Holetype'] = relationship('Holetype', back_populates='hole')
    theholelevel: Mapped['Theholelevel'] = relationship('Theholelevel', back_populates='hole')
    holetrace: Mapped[list['Holetrace']] = relationship('Holetrace', secondary='hole_holetrace', back_populates='hole')


class Holetrace(Base):
    __tablename__ = 'holetrace'
    __table_args__ = (
        ForeignKeyConstraint(['action_type'], ['actiontype.id'], ondelete='CASCADE', name='holetrace_action_type_fkey'),
        ForeignKeyConstraint(['currency_type'], ['currencytype.id'], ondelete='CASCADE', name='holetrace_currency_type_fkey'),
        ForeignKeyConstraint(['from_currency'], ['currencytype.id'], ondelete='SET NULL', name='holetrace_from_currency_fkey'),
        ForeignKeyConstraint(['source_account'], ['account.id'], ondelete='CASCADE', name='holetrace_source_account_fkey'),
        ForeignKeyConstraint(['trace_type'], ['tracetype.id'], ondelete='CASCADE', name='holetrace_trace_type_fkey'),
        PrimaryKeyConstraint('id', name='holetrace_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_account: Mapped[int] = mapped_column(Integer, nullable=False)
    action_type: Mapped[int] = mapped_column(Integer, nullable=False)
    currency_type: Mapped[int] = mapped_column(Integer, nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    trace_type: Mapped[int] = mapped_column(Integer, nullable=False)
    execute_at_fx_rate: Mapped[Optional[float]] = mapped_column(Double(53))
    realtime_fx_rate: Mapped[Optional[float]] = mapped_column(Double(53))
    from_currency: Mapped[Optional[int]] = mapped_column(Integer)
    amount: Mapped[Optional[float]] = mapped_column(Double(53))

    hole: Mapped[list['Hole']] = relationship('Hole', secondary='hole_holetrace', back_populates='holetrace')
    actiontype: Mapped['Actiontype'] = relationship('Actiontype', back_populates='holetrace')
    currencytype: Mapped['Currencytype'] = relationship('Currencytype', foreign_keys=[currency_type], back_populates='holetrace')
    currencytype_: Mapped[Optional['Currencytype']] = relationship('Currencytype', foreign_keys=[from_currency], back_populates='holetrace_')
    account: Mapped['Account'] = relationship('Account', back_populates='holetrace')
    tracetype: Mapped['Tracetype'] = relationship('Tracetype', back_populates='holetrace')


t_hole_holetrace = Table(
    'hole_holetrace', Base.metadata,
    Column('hole', Uuid, primary_key=True),
    Column('holetrace', Integer, primary_key=True),
    ForeignKeyConstraint(['hole'], ['hole.id'], name='hole_holetrace_hole_fkey'),
    ForeignKeyConstraint(['holetrace'], ['holetrace.id'], name='hole_holetrace_holetrace_fkey'),
    PrimaryKeyConstraint('hole', 'holetrace', name='hole_holetrace_pkey')
)
